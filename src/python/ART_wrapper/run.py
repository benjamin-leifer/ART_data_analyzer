"""
this module runs ART simulations by set up the ART input files for each MD dump file sample, 
create a run_dir associated with the central_atom id, 
copy all modified input files into each run_dir, run ./bart.sh under each run_dir
by subprocess module in parallel
"""
import subprocess
import os
import re
import json
import shutil
import multiprocessing as mp
from data_reader import *


def run_art_mp(path_to_data_dir, input_param, pbs=False):
	"""
	this function will run art by bart.sh inside the path_to_data_dir for each path_to_run_dir
	in a parallel fashion
	"""
	
	num_of_proc = input_param["num_of_proc"]
	central_atom_list = input_param['central_atom_list']
	
	pool = mp.Pool(processes=num_of_proc)
		
	list_of_run_dir = []
	for central_atom in central_atom_list:
		path_to_run_dir = os.path.join(path_to_data_dir, str(central_atom))
		list_of_run_dir.append(path_to_run_dir)
	pool.map(run_bart,list_of_run_dir)
	print "done running ART!"

def run_bart(path_to_run_dir):
	# run bart.sh inside each dir
	os.chdir(path_to_run_dir)
	subprocess.check_call("chmod +x mod_bart.sh; ./mod_bart.sh", shell=True)
	print "done runing art for %s"%path_to_run_dir
	

def set_up_input_files(path_to_data_dir, input_param):
	"""
	this function will set up the input files for each MD dump file sample,
	, create a run_dir associated with the central_atom id,
	copy all modified input files into each run_dir,
	run bart.sh under each run_dir
	
	directory structure: 
	
	# path_to_input_files are saved in the $ART_INPUT
	# path_to_data_dir = path_to_root_dir + sample_name
	# path_to_run_dir = path_to_data_dir + %d%central_atom_id
	
	path_to_input_files = "/Users/ltian/ART_sample/Cu64Zr36/10E11/"
	path_to_root_dir = path_to_input_files + 'art'
	total_energy = -46021.0583322591
	box_dim = [54.2654] * 3
	sample_name = "dump_10E11"
	set_up_input_files(path_to_data_dir, input_param)
	"""
	path_to_input_files = input_param['path_to_input_files']
	total_energy = input_param['total_energy']
	box_dim = input_param['box_dim']
	box_range = input_param['box_range']
	sample_name = input_param['sample_name']
	sample_type = input_param['sample_type']
	
	central_atom_list = input_param['central_atom_list']
	
	if not os.path.isdir(path_to_data_dir):
		os.makedirs(path_to_data_dir)	
	
	# obtain the refconfig file from the dump or lammps data file, need total energy, box_dim
	if sample_type == 'dump':
		dump_to_refconfig(path_to_input_files, sample_name, total_energy, box_dim, box_range)
	elif sample_type == 'lammps_data':
		data_to_refconfig(path_to_input_files, sample_name, total_energy, box_dim)
	else:
		raise Exception('the sample type can be either dump or lammps_data, please select the correct sample!')
	potential_file = raw_input("Please type the potential file name:")
	# manual: modify the in.lammps file 1) modify the dump file name of read_dump
	# 2) modify potential file string
	
	for central_atom in central_atom_list:
		path_to_run_dir = os.path.join(path_to_data_dir, str(central_atom))
		# create a directory for each central_atom id under path_to_data_dir = path_to_root_dir + sample_name
		if not os.path.isdir(path_to_run_dir):
			os.makedirs(path_to_run_dir)
		# modify the central_atom in bart.sh, with iteration from central_atom_list
		modify_bart(path_to_input_files, central_atom)
		# copy all modified files into the path_to_run_dir, mod_bart.sh,
		# src_files = os.listdir(path_to_input_files)
		#for file_name in src_files:
		for file_name in ['mod_bart.sh','refconfig',input_param['sample_name'],"in.lammps",potential_file]:
		#if file_name == 'bart.sh' or file_name == "central_atom_list.json" or file_name == "interested_atom_list.json":
		#	continue
			full_file_name = os.path.join(path_to_input_files, file_name)
			if (os.path.isfile(full_file_name)):
				shutil.copy(full_file_name, path_to_run_dir)
	print "finished setting up ART run dir and input files!"
	
	
def modify_bart(path_to_input_files, central_atom_id):
	"""
	this function takes the bart.sh in path_to_input_files and modify the central_atom
	then return the modified string file to be ready saved into a file 
	"""
	path_to_bart = os.path.join(path_to_input_files,'bart.sh')
	with open(path_to_bart, 'r') as f:
		data = f.read()
	pattern = "(setenv[\s]+Central_Atom[\s]+)([\d]+)"
	modified_bart = re.sub(pattern, r"\g<1>%s"%str(central_atom_id), data)
	
	path_to_mod_bart = os.path.join(path_to_input_files,'mod_bart.sh')
	with open(path_to_mod_bart, 'w') as f:
		f.write(modified_bart)
		f.close()
    
def data_to_refconfig(path_to_input_files, sample_name, total_energy, box_dim):
	"""
	this function takes the data in the lammps data file and converts into 
	a refconfig file with periodic boundary condition
	refconfig file examples all used the absolute coordinates
	This is preferred way
	"""
	path_to_data = os.path.join(path_to_input_files, sample_name)
	
	result = read_data_from_lammps_data(path_to_data)
	
	df = result[['atom_id', 'x','y','z']]
	df.insert(loc=0, column='1', value='')
	file_to_save = os.path.join(path_to_input_files,'refconfig')
	with open(file_to_save, 'w') as f:
		f.write(' run_id: 1000\n total_energy: %s \n P %s %s %s\n'%(total_energy, box_dim[0],box_dim[1],box_dim[2]))
		df.to_csv(f, header=False, index=False, sep=' ')
		f.close()
	print "saving refconfig in %s"%path_to_input_files	

def dump_to_refconfig(path_to_input_files, sample_name, total_energy, box_dim, box_range, fractional_coordinates=True):
	"""
	this function takes a dump file and modify the dump file to a refconfig
	file for periodic boundary condition
	path_to_input_files = "/Users/ltian/ART_sample/Cu64Zr36/10E11/"
	sample_name= "dump_10E11"
	total_energy = -46021.0583322591
	box_dim = [54.2654] * 3
	dump_to_refconfig(path_to_input_files, sample_name, total_energy, box_dim)
	"""
	path_to_dump = os.path.join(path_to_input_files,sample_name)
	result = read_data_from_dump(path_to_dump)
	df = result[['atom_id', 'x','y','z']]
	df.insert(loc=0, column='1', value='')
	# the atomic coordinates in dump file are fractional coordinates
	# the actual coordinates are (x_s * box_dim[0]) + box_range_x_start,...
	if fractional_coordinates == True:
		df.update((df[['x','y','z']] * box_dim) + [box_range[0][0],box_range[1][0],box_range[2][0]])
	file_to_save = os.path.join(path_to_input_files,'refconfig')
	with open(file_to_save, 'w') as f:
		f.write(' run_id: 1000\n total_energy: %s \n P %s %s %s\n'%(total_energy, box_dim[0],box_dim[1],box_dim[2]))
		df.to_csv(f, header=False, index=False, sep=' ')
		f.close()
	print "saving refconfig in %s"%path_to_input_files
