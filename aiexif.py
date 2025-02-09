import sys
import json
from PIL import Image
from PIL.PngImagePlugin import PngInfo

def extract_ai_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            meta_dict = {}
            
            # 读取PNG原生元数据
            if hasattr(img, 'text'):
                meta_dict.update(img.text)
            
            # 尝试读取Photoshop格式元数据
            if hasattr(img, 'info') and 'photoshop' in img.info:
                try:
                    photoshop_meta = img.info['photoshop']
                    if isinstance(photoshop_meta, bytes):
                        meta_dict['Photoshop'] = photoshop_meta.decode('utf-8', errors='ignore')
                except Exception as e:
                    pass
            
            # 优先检查常见AI工具元数据字段
            possible_fields = [
                'parameters',  # Stable Diffusion
                'Comment',     # 常见格式
                'Description', # 其他工具
                'UserComment', # EXIF标准
                'prompt',      # 某些定制格式
                'workflow'     # ComfyUI
            ]

            extracted_data = {}
            for field in possible_fields:
                if field in meta_dict:
                    # 尝试解析JSON格式
                    if field in ['workflow']:
                        try:
                            extracted_data[field] = json.loads(meta_dict[field])
                        except json.JSONDecodeError:
                            extracted_data[field] = meta_dict[field]
                    else:
                        extracted_data[field] = meta_dict[field]
                    # 如果找到关键参数则提前返回
                    if field == 'parameters':
                        return process_parameters(extracted_data[field])
            
            # 如果没有找到标准字段，尝试自动检测
            for value in meta_dict.values():
                if "Steps: " in value and "Sampler: " in value:
                    return process_parameters(value)
            
            return extracted_data if extracted_data else "未找到生成参数"

    except Exception as e:
        return f"读取文件出错: {str(e)}"

def process_parameters(parameters):
    """解析常见的参数格式"""
    result = {}
    
    # 分割基本参数
    parts = parameters.split('Negative prompt: ')
    result['prompt'] = parts[0].strip()
    
    if len(parts) > 1:
        negative_parts = parts[1].split('Steps:')
        result['negative_prompt'] = negative_parts[0].strip()
        params_str = negative_parts[1] if len(negative_parts) > 1 else ''
    else:
        params_str = parts[0].split('Steps:')[-1]
    
    # 解析参数键值对
    param_pairs = [pair for pair in params_str.split(', ') if ':' in pair]
    for pair in param_pairs:
        key, value = pair.split(':', 1)
        result[key.strip()] = value.strip()
    
    return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python read_ai_meta.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    metadata = extract_ai_metadata(image_path)
    
    print("\n提取到的元数据信息：")
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            print(f"{key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"  {value}")
    else:
        print(metadata)
