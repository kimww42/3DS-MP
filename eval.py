from tqdm import tqdm
import torch
from neural_style_field import NeuralStyleField
import numpy as np
import random
import torchvision
import os
import argparse
from pathlib import Path
import open3d as o3d
from sg_render import compute_envmap
import imageio
import os.path as osp
from torchvision import transforms

import clip
from utils import clip_model
from utils import device
from PIL import Image

def get_clip_r_precision(args):
    # Load CLIP model
    clip_model, preprocess = clip.load(args.clipmodel, device, jit=args.jit)

    if args.prompt:
        # prompt = ' '.join("yellow car with yellow spoiler")
        # prompt2 = ' '.join("yellow car with red spoiler")
        prompt = ' '.join(args.prompt)
        prompt2 = ' '.join(args.prompt2)
        prompt3 = ' '.join(args.prompt3)
        prompt4 = ' '.join(args.prompt4)
        prompt5 = ' '.join(args.prompt5)

        prompt_token = clip.tokenize([prompt]).to(device)
        prompt2_token = clip.tokenize([prompt2]).to(device)
        prompt3_token = clip.tokenize([prompt3]).to(device)
        prompt4_token = clip.tokenize([prompt4]).to(device)
        prompt5_token = clip.tokenize([prompt5]).to(device)

        encoded_text = clip_model.encode_text(prompt_token)
        encoded_text2 = clip_model.encode_text(prompt2_token)
        encoded_text3 = clip_model.encode_text(prompt3_token)
        encoded_text4 = clip_model.encode_text(prompt4_token)
        encoded_text5 = clip_model.encode_text(prompt5_token)

        # Save prompt
        with open(os.path.join(args.output_dir, prompt), "w") as f:
            f.write("")

        norm_encoded = encoded_text


    if args.clipmodel == "ViT-B/32" : 
        res = 224
    elif args.clipmodel == "ViT-L/14@336px" :
        res = 336

    augment_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.RandomResizedCrop(res, scale=(1, 1)), #Obtain a thumbnail image to meet the requirements of clip's input image size
    ])
    
    sim_real = 0
    sim_2 = 0
    sim_3 = 0
    sim_4 = 0
    sim_5 = 0

    for i in range(8):
        image = Image.open(args.output_dir + '/rgb/iter_test_rgb_' + str(i).zfill(3) + '.jpg')
        # import pdb; pdb.set_trace()
        image = augment_transform(image).unsqueeze(0).to(device)
        encoded_image = clip_model.encode_image(image)
        sim_real += torch.cosine_similarity(torch.mean(encoded_image, dim=0), torch.mean(encoded_text, dim=0), dim=0).item()
        sim_2 += torch.cosine_similarity(torch.mean(encoded_image, dim=0), torch.mean(encoded_text2, dim=0), dim=0).item()
        sim_3 += torch.cosine_similarity(torch.mean(encoded_image, dim=0), torch.mean(encoded_text3, dim=0), dim=0).item()
        sim_4 += torch.cosine_similarity(torch.mean(encoded_image, dim=0), torch.mean(encoded_text4, dim=0), dim=0).item()
        sim_5 += torch.cosine_similarity(torch.mean(encoded_image, dim=0), torch.mean(encoded_text5, dim=0), dim=0).item()

    sim_real /= 8
    sim_2 /= 8
    sim_3 /= 8
    sim_4 /= 8
    sim_5 /= 8

    print(sim_real, sim_2, sim_3, sim_4, sim_5)
    
        # 변수 이름과 값을 딕셔너리에 저장
    variables = {'a': sim_real, 'b': sim_2, 'c': sim_3, 'd': sim_4, 'e': sim_5}

    # 변수의 값을 기준으로 정렬하여 상위 3개 선택
    top_3 = sorted(variables.items(), key=lambda item: item[1], reverse=True)[:3]

        # 상위 3개의 변수 이름 추출
    top_3_names = [name for name, value in top_3]

    # 'a'가 상위 3개 안에 있는지 확인
    if 'a' in top_3_names:
        with open(os.path.join(args.output_dir, f'rrr_{args.clipmodel[:5]}_top3_yes'), "w") as f:
            f.write("")
        
    if (max(sim_real, sim_2, sim_3, sim_4, sim_5) == sim_real) :
        with open(os.path.join(args.output_dir, f'rrr_{args.clipmodel[:5]}_top1_yes'), "w") as f:
            f.write("")
    
    with open(os.path.join(args.output_dir, f'rrr_{args.clipmodel[:5]}_{sim_real}_clipscore'), "w") as f:
            f.write("")



def save_gif(dir,fps):
    imgpath = dir
    frames = []
    for idx in sorted(os.listdir(imgpath)):
        print(idx)
        img = osp.join(imgpath,idx)
        frames.append(imageio.imread(img))
    imageio.mimsave(os.path.join(dir, 'eval.gif'),frames,'GIF',duration=1/fps)

def get_normalize_mesh(pro_path):
    mesh = o3d.io.read_triangle_mesh(pro_path)
    vertices = np.asarray(mesh.vertices)
    shift = np.mean(vertices,axis=0)
    scale = np.max(np.linalg.norm(vertices-shift, ord=2, axis=1))
    vertices = (vertices-shift) / scale
    mesh.vertices = o3d.cuda.pybind.utility.Vector3dVector(vertices)
    return mesh

def test(args):
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    torch.set_default_dtype(torch.float32)
    # torch.set_num_threads(8)
    # Constrain all sources of randomness
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    objbase, extension = os.path.splitext(os.path.basename(args.obj_path))
    # Check that isn't already done
    if (not args.overwrite) and os.path.exists(os.path.join(args.output_dir, "loss.png")) and \
            os.path.exists(os.path.join(args.output_dir, f"{objbase}_final.obj")):
        print(f"Already done with {args.output_dir}")
        exit()
    elif args.overwrite and os.path.exists(os.path.join(args.output_dir, "loss.png")) and \
            os.path.exists(os.path.join(args.output_dir, f"{objbase}_final.obj")):
        import shutil
        for filename in os.listdir(args.output_dir):
            file_path = os.path.join(args.output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    n_augs = args.n_augs
    dir = args.output_dir
    os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
    
    model = NeuralStyleField(args.material_random_pe_numfreq,
                             args.material_random_pe_sigma,
                             args.num_lgt_sgs,
                             args.max_delta_theta,
                             args.max_delta_phi,
                             args.normal_nerf_pe_numfreq,
                             args.normal_random_pe_numfreq,
                             args.symmetry,
                             args.radius,
                             args.background,
                             args.init_r_and_s,
                             args.width,
                             args.init_roughness,
                             args.init_specular,
                             args.material_nerf_pe_numfreq,
                             args.normal_random_pe_sigma,
                             args.if_normal_clamp
                            )
    state_dict = torch.load(args.output_dir + '/iter1500.pth')
    model_state_dict = model.state_dict()

    # 예상치 못한 키 제거
    for key in list(state_dict['model'].keys()):
        if key not in model_state_dict:
            del state_dict['model'][key]

    # 수정된 state_dict 로드
    model.load_state_dict(state_dict['model'], strict=False)
    
    model.eval()
    envmap = compute_envmap(lgtSGs=model.svbrdf_network.get_light(), H=256, W=512, upper_hemi=model.svbrdf_network.upper_hemi)
    envmap = envmap.cpu().numpy()
    imageio.imwrite(os.path.join(dir, 'envmap.exr'), envmap)
    if torch.cuda.is_available():
        model.cuda()
    mesh = get_normalize_mesh(args.obj_path)
    mesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(mesh)  
    if not os.path.exists(dir):
        os.makedirs(dir)   

    dir_rgb = os.path.join(dir, 'rgb')
    dir_normal1 = os.path.join(dir, 'normal1')
    dir_normal2 = os.path.join(dir, 'normal2')
    dir_roughness = os.path.join(dir, 'roughness')
    dir_diffuse = os.path.join(dir, 'diffuse')
    dir_specular = os.path.join(dir, 'specular')
    if not os.path.exists(dir_rgb):
        os.makedirs(dir_rgb)
    if not os.path.exists(dir_normal1):
        os.makedirs(dir_normal1)
    if not os.path.exists(dir_normal2):
        os.makedirs(dir_normal2)
    if not os.path.exists(dir_roughness):
        os.makedirs(dir_roughness)
    if not os.path.exists(dir_diffuse):
        os.makedirs(dir_diffuse)
    if not os.path.exists(dir_specular):
        os.makedirs(dir_specular)
    if args.render_singer_view:
        view_num=1
    if args.render_gif:
        view_num=8
    if view_num == 8:
        azim = torch.linspace(0, 2 * np.pi, view_num + 1)[:-1]  # since 0 = 2π dont include last element
        elev = torch.tensor(args.frontview_center[1])    
        for i in tqdm(range(view_num)):   
        
            rendered_images ,normal1 , normal2 ,roughness, diffuse, specular= model.render_single_image(scene=scene, 
                                        azim=azim[i],
                                        elev=elev
                                        )
        
            torchvision.utils.save_image(rendered_images, os.path.join(dir_rgb, f'iter_test_rgb_{i:03d}.jpg'))
            torchvision.utils.save_image(normal1, os.path.join(dir_normal1, f'iter_test_normal1_{i:03d}.jpg'))
            torchvision.utils.save_image(normal2, os.path.join(dir_normal2, f'iter_test_normal2_{i:03d}.jpg'))
            torchvision.utils.save_image(roughness, os.path.join(dir_roughness, f'iter_test_roughness_{i:03d}.jpg'))
            torchvision.utils.save_image(diffuse, os.path.join(dir_diffuse, f'iter_test_diffuse_{i:03d}.jpg'))
            torchvision.utils.save_image(specular, os.path.join(dir_specular, f'iter_test_specular_{i:03d}.jpg'))
        save_gif(dir_rgb,30)
        save_gif(dir_normal1,30)
        save_gif(dir_normal2,30)
        save_gif(dir_roughness,30)
        save_gif(dir_specular,30)
        save_gif(dir_diffuse,30)
    if view_num == 1:
        azim = torch.tensor(args.frontview_center[0])
        elev = torch.tensor(args.frontview_center[1])   
        for i in tqdm(range(view_num)):   
        
            rendered_images ,normal1 , normal2 ,roughness, diffuse, specular= model.render_single_image(scene=scene, 
                                        azim=azim,
                                        elev=elev
                                        )
        
            torchvision.utils.save_image(rendered_images, os.path.join(dir_rgb, f'1iter_test_rgb_{i:03d}.jpg'))
            torchvision.utils.save_image(normal1, os.path.join(dir_normal1, f'1iter_test_normal1_{i:03d}.jpg'))
            torchvision.utils.save_image(normal2, os.path.join(dir_normal2, f'1iter_test_normal2_{i:03d}.jpg'))
            torchvision.utils.save_image(roughness, os.path.join(dir_roughness, f'1iter_test_roughness_{i:03d}.jpg'))
            torchvision.utils.save_image(diffuse, os.path.join(dir_diffuse, f'1iter_test_diffuse_{i:03d}.jpg'))
            torchvision.utils.save_image(specular, os.path.join(dir_specular, f'1iter_test_specular_{i:03d}.jpg'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_lgt_sgs', type=int, default=32) #the number of light SGs
    parser.add_argument('--max_delta_theta', type=float, default=1.5707) #maximum offset of elevation angle whose unit is radian
    parser.add_argument('--max_delta_phi', type=float, default=1.5707) #maximum offset of azimuth angle whose unit is radian
    
    parser.add_argument('--normal_nerf_pe_numfreq',  type=int, default=0) #the number of frequencies using nerf's position encoding in normal network
    parser.add_argument('--normal_random_pe_numfreq', type=int, default=0) #the number of frequencies using random position encoding in normal network
    parser.add_argument('--normal_random_pe_sigma', type=float, default=20.0) #the sigma of random position encoding in normal network
    parser.add_argument('--material_nerf_pe_numfreq',  type=int, default=0) #the numer of frequencies using nerf's position encoding in svbrdf network
    parser.add_argument('--material_random_pe_numfreq', type=int, default=0) #the numer of frequencies using random position encoding in svbrdf network
    parser.add_argument('--material_random_pe_sigma', type=float, default=20.0) #the sigma of random position encoding in svbrdf network
    parser.add_argument('--if_normal_clamp', action='store_true') 
    
    parser.add_argument('--init_r_and_s', action='store_true') #It will initialize roughness and specular if setting true
    parser.add_argument('--init_roughness', type=float, default=0.7) #Initial value of roughness 0~1
    parser.add_argument('--init_specular', type=float, default=0.23)  #Initial value of specular 0~1
    parser.add_argument('--width', type=int, default=512) #the size of render image will be [width,width]
    
    parser.add_argument('--radius', type=float, default=2.0) #the sampling raidus of camara position
    parser.add_argument('--background', type=str, default='black') #the background of render image.'black','white' or 'gaussian' can be selected
    parser.add_argument('--local_percentage',type=float, default=0.7) #percent threshold of the object's mask in cropped image.It will be cropped again
                                                                      #if the proportion of the object's mask in cropped image is less than this threshold.
    parser.add_argument('--clipmodel', type=str, default='ViT-B/32')
    parser.add_argument('--jit', action="store_true")                                                                 #This parameter can effectively prevent image degradation
    parser.add_argument('--obj_path', type=str, default='meshes/mesh1.obj') #the storage path of raw or original mesh
    parser.add_argument('--prompt', nargs="+", default='a pig with pants') #the text prompt to style a raw mesh
    parser.add_argument('--prompt2', nargs="+", default='a pig with pants') #the text prompt to style a raw mesh
    parser.add_argument('--prompt3', nargs="+", default='a pig with pants') #the text prompt to style a raw mesh
    parser.add_argument('--prompt4', nargs="+", default='a pig with pants') #the text prompt to style a raw mesh
    parser.add_argument('--prompt5', nargs="+", default='a pig with pants') #the text prompt to style a raw mesh

    parser.add_argument('--output_dir', type=str, default='round2/alpha5') #directory where the results will be saved
    parser.add_argument('--learning_rate', type=float, default=0.0005)
    parser.add_argument('--lr_decay', type=float, default=1) #decay factor of learning rate
    parser.add_argument('--n_views', type=int, default=4) #number of viewpoints optimized at the same time in an iteration
    parser.add_argument('--n_augs', type=int, default=0) #In one iteration, the gradient retrieval times of the rendered thumbnail
    parser.add_argument('--n_normaugs', type=int, default=0) #In one iteration, the gradient retrieval times of the local clip of the rendered image
    parser.add_argument('--n_iter', type=int, default=1501) #number of iterations

    parser.add_argument('--frontview_std', type=float, default=8) # Angular variance of the off-center view
    parser.add_argument('--frontview_center', nargs=2, type=float, default=[0., 0.]) #Center position of viewpoint.[azimuth angle(0~2π),elevation angle(0~π)]
    parser.add_argument('--clipavg', type=str, default=None)
    parser.add_argument('--mincrop', type=float, default=1) #minimium clipping scale in 2D augmentation 
    parser.add_argument('--maxcrop', type=float, default=1) #maximium clipping scale in 2D augmentation
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--seed', type=int, default=0) #random seed
    parser.add_argument('--symmetry', default=False, action='store_true') #With this symmetry prior, the texture of the mesh 
                                                                          #will be symmetrical along the z-axis.We use this parameter in person
    parser.add_argument('--decayfreq', type=int, default=None) #decay freaquency of learning rate

    parser.add_argument('--model_dir', type=str, default=None) # directory of the checkpopoint
    parser.add_argument('--render_singer_view', action='store_true') # Render a single picture from a certain perspective,e.g. frontview_center
    parser.add_argument('--render_gif', action='store_true') #Render under a bunch of new viewpoints, and synthesize these viewpoints into gif
    args = parser.parse_args()

    test(args)
    get_clip_r_precision(args)