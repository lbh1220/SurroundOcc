import pickle
import os

# 你的原始 val.pkl 路径
input_pkl = 'data/nuscenes_infos_val.pkl'
# 新的筛选后 pkl 路径
output_pkl = 'data/nuscenes_infos_val_filtered.pkl'

with open(input_pkl, 'rb') as f:
    data = pickle.load(f)

# data 是 dict，data['infos'] 是 list
infos = data['infos']
metadata = data.get('metadata', {})

filtered = []
missing = 0

for idx, sample in enumerate(infos):
    occ_path = sample.get('occ_path', None)
    if not occ_path or not os.path.exists(occ_path):
        missing += 1
        continue

    cams = sample.get('cams', {})
    all_cams_exist = True
    for cam_name, cam_info in cams.items():
        img_path = cam_info.get('data_path', None)
        if not img_path or not os.path.exists(img_path):
            all_cams_exist = False
            break

    if all_cams_exist:
        filtered.append(sample)
    else:
        missing += 1

print(f"Total samples: {len(infos)}")
print(f"Valid samples: {len(filtered)}")
print(f"Missing samples: {missing}")

# 保存结构要和原来一样
new_data = {
    'infos': filtered,
    'metadata': metadata
}

with open(output_pkl, 'wb') as f:
    pickle.dump(new_data, f)

print(f"Filtered pkl saved to: {output_pkl}")