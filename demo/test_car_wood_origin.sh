python main_siwon.py \
--obj_path data/source_meshes/car_face64962.obj \
--output_dir results/demo/car/lambo_red \
--prompt "yellow car;with red spoiler"  \
--normal_nerf_pe_numfreq 10  \
--init_r_and_s \
--init_roughness 0.5 \
--width 512 \
--local_percentage 0.7 \
--background 'black' \
--radius 2  \
--n_views 3 \
--material_nerf_pe_numfreq 12 \
--num_lgt_sgs 32 \
--n_normaugs 4 \
--n_augs 1  \
--frontview_std 12 \
--clipavg view \
--lr_decay 0.7 \
--mincrop 0.01 \
--maxcrop 0.05 \
--seed 150 \
--n_iter 1501 \
--learning_rate 0.0005 \
--frontview_center 1.96349 0.6283 \

python eval.py \
--obj_path data/source_meshes/car_face64962.obj \
--output_dir results/demo/car/lambo_red \
--prompt "yellow car;with red spoiler"  \
--normal_nerf_pe_numfreq 10  \
--init_r_and_s \
--init_roughness 0.5 \
--width 512 \
--local_percentage 0.7 \
--background 'black' \
--radius 2  \
--n_views 3 \
--material_nerf_pe_numfreq 12 \
--num_lgt_sgs 32 \
--n_normaugs 4 \
--n_augs 1  \
--frontview_std 12 \
--clipavg view \
--lr_decay 0.7 \
--mincrop 0.01 \
--maxcrop 0.05 \
--seed 150 \
--n_iter 1501 \
--learning_rate 0.0005 \
--frontview_center 1.96349 0.6283 \
--model_dir results/demo/car/lambo/iter1500.pth \
--render_gif
