import os
import json

def convert_filename(dir_path):    
    for file_name in os.listdir(dir_path):
        print(file_name)
        if ".json" not in file_name:
            continue
        fp = os.path.join(dir_path, file_name)
        with open(fp, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        new_dir_path = dir_path + "/converted"
        
        os.mkdir(new_dir_path) if not os.path.exists(new_dir_path) else None

        new_fp = os.path.join(new_dir_path, file_name.replace(" ", "_").replace("(", "_").replace(")", "_"))
        with open(new_fp, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        

if __name__ == "__main__":
    dir_path = "./data/data"
    convert_filename(dir_path)


