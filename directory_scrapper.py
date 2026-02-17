import json
from pathlib import Path

def get_directory_data(target_directory, exclude_list):
    root = Path(target_directory)
    data_list = []

    if not root.exists():
        print("The specified directory does not exist.")
        return []

    for item in root.rglob('*'):
        # Skip excluded folders
        if any(ex in item.parts for ex in exclude_list):
            continue
            
        item_type = "Folder" if item.is_dir() else "File"
        content = "<no content>"
        
        if item.is_file():
            try:
                # Read full text content
                text = item.read_text(encoding='utf-8', errors='ignore').strip()
                content = text if text else "<empty file>"
            except Exception:
                content = "<no content (unreadable/binary)>"

        item_dict = {
            "Type": item_type,
            "Path": str(item),
            "Content": content
        }
        data_list.append(item_dict)
    
    return data_list

def save_to_json(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # indent=4 makes the JSON file readable to humans
            json.dump(data, f, indent=4)
        print(f"Successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":
    # Settings
    folders_to_skip = ['.git', '__pycache__', '.venv', 'myenv', 'node_modules']
    output_filename = 'directory_data.json'
    
    # 1. Get the data
    results = get_directory_data('.', folders_to_skip)
    
    # 2. Save to JSON file
    save_to_json(results, output_filename)
    
    # 3. Optional: Print the dict to console to see it worked
    print(f"Total items indexed: {len(results)}")