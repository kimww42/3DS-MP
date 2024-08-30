 # <p align="center"> <font color=#008000>Accurate 3D Stylization with Multiple Prompt</p>

 #####  <p align="center"> [Siwon Kim](github.com/kimww42)</p>

#### <p align="center"> 2024 하계계절 <font color=#dd0000>자기주도연구1</font></p>

<p align="center">
  <img width="100%" src="https://github.com/Gorilla-Lab-SCUT/tango/blob/main/tango_assets/stylization.gif"/>
</p>

### Installation

**Note:** You can directly pull the image we uploaded to AliCloud
```
docker pull registry.cn-shenzhen.aliyuncs.com/baopin/t2m:1.7
```

### System Requirements
- Python >=3.7 and <=3.9
- CUDA 11
- Nvidia GPU with 12 GB ram at least
- Open3d >=0.14.1
- the package of clip (https://github.com/openai/CLIP)

### Train
Call the below shell scripts to generate example styles. 
```bash
# shoe made of gold
./demo/run_shoe_gold.sh
# vase made of wicker 
./demo/run_vase_wicker.sh
# car made of wood
./demo/run_car_wood_origin.sh
# ...
```
The outputs will be saved to `results/demo`

### Validate
Call the below shell scripts to generate gif. 
```bash
# shoe made of gold
./demo/test_shoe_gold.sh
# vase made of wicker 
./demo/test_vase_wicker.sh
# car made of wood
./demo/test_car_wood_origin.sh
# ...
```
<!-- <p align="center">
  <img width="100%" src="./tango_assets/method.jpg"/>
</p> -->
