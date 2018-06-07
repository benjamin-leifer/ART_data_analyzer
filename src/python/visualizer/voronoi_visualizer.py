"""
this vornoi visualization module plot the statistical distribution of voronoi classes
i.e, ico, ico-like, GUMs
"""
import os
import json
import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cmx
from mpl_toolkits.mplot3d import Axes3D
from data_reader import *
import scipy.interpolate

def plot_voronoi_histogram_3(path_to_image, x):
	"""
	Input:
	path_to_image: string
		string that specifies the path to save the image
	x: list
		a three element list, each element is an array-like
	
	"""
	plt.figure()
	#fig, ax = plt.subplots()
	#weights = [np.ones_like(x[0])/float(len(x[0])), np.ones_like(x[1])/float(len(x[1])), np.ones_like(x[2])/float(len(x[2]))]
	plt.hist(x, bins=10, color=['r','b','black'],label=["initial","saddle","final"])
	x1 = [0,1,2]
	labels = ["ico","ico-like","GUM"]
	#ax.set_xticks(x1)
	#ax.set_xticklabels(labels)
	plt.xticks(x1, labels)
	plt.legend(loc='best')
	plt.savefig(path_to_image)
	plt.close()

def voronoi_scatter_3d(path_to_curr_event, path_to_config):
	path_to_voro_results = path_to_curr_event + "/voronoi_index_results.json"
	path_to_image = path_to_curr_event + "/voronoi_3D_scatter.png"
	initial_config = read_data_from_file(path_to_config)
	x,y,z = initial_config['x'].tolist(),initial_config['y'].tolist(),initial_config['z'].tolist()
	voro_results = json.load(open(path_to_voro_results,'r'))
	init_voronoi_index = voro_results["init"]
	cs = classify_voronoi_index(init_voronoi_index)
	scatter3d(path_to_image, x,y,z,cs, colorsMap='jet')

def voronoi_contour_2d(path_to_curr_event, path_to_config,cut_plane='xy',cut_position=0.5,cut_tol = 0.05):
	path_to_voro_results = path_to_curr_event + "/voronoi_index_results.json"
	path_to_image = path_to_curr_event + "/voronoi_2D_contour.png"
	initial_config = read_data_from_file(path_to_config)
	x,y,z = initial_config['x'].tolist(),initial_config['y'].tolist(),initial_config['z'].tolist()
	if cut_plane == 'xy':
		cut_position = cut_position * (min(z) + max(z))
		cut_tolerance = cut_tol * (max(z) - min(z))
		min_cut_range = cut_position - cut_tolerance
		max_cut_range = cut_position + cut_tolerance
		i=0
		region_index = []
		for z_c in z:
			if z_c >= min_cut_range and z_c <= max_cut_range:
				region_index.append(i)
			i = i + 1
		c_x = [x[i] for i in region_index]
		c_y = [y[i] for i in region_index]
	elif cut_plane == 'xz':
		cut_position = cut_position * (min(y) + max(y))
		cut_tolerance = cut_tol * (max(y) - min(y))
		min_cut_range = cut_position - cut_tolerance
		max_cut_range = cut_position + cut_tolerance
		i=0
		region_index = []
		for y_c in y:
			if y_c >= min_cut_range and y_c <= max_cut_range:
				region_index.append(i)
			i = i + 1
		c_x = [x[i] for i in region_index]
		c_y = [z[i] for i in region_index]
	elif cut_plane == 'yz':
		cut_position = cut_position * (min(x) + max(x))
		cut_tolerance = cut_tol * (max(x) - min(x))
		min_cut_range = cut_position - cut_tolerance
		max_cut_range = cut_position + cut_tolerance
		i=0
		region_index = []
		for x_c in x:
			if x_c >= min_cut_range and x_c <= max_cut_range:
				region_index.append(i)
			i = i + 1
		c_x = [y[i] for i in region_index]
		c_y = [z[i] for i in region_index]		
	voro_results = json.load(open(path_to_voro_results,'r'))
	init_voronoi_index = voro_results["init"]
	voro_class = classify_voronoi_index(init_voronoi_index)
	cs = [voro_class[i] for i in region_index]
	
	f_x,f_y = np.meshgrid(c_x,c_y)
	rbf = scipy.interpolate.Rbf(c_x, c_y, cs, function='linear')
	f_z = rbf(f_x, f_y)
	
	plt.figure()
	plt.imshow(f_z, vmin=min(cs), vmax=max(cs), origin='lower',\
	extent=[min(c_x), max(c_x), min(c_y), max(c_y)])
	cm = plt.get_cmap('jet')
	plt.scatter(c_x, c_y, c=cs,cmap=cm)
	plt.colorbar()
	#CS = plt.contour(c_x,c_y,cs,colorsMap='jet')
	#plt.clabel(CS, inline=1, fontsize=10)
	plt.title('solid-like, transition, liquid-like')
	plt.savefig(path_to_image)
	#scatter3d(path_to_image, x,y,z,cs, colorsMap='jet')
# another voronoi index classification
global ICO
ICO = [[0,6,0,0],[0,5,2,0],[0,4,4,0],[0,3,6,0],[0,2,8,0],[0,2,8,1],[0,0,12,0],[0,1,10,2],[0,0,12,2],[0,0,12,3],[0,0,12,4],[0,0,12,5]]
global ICO_LIKE
ICO_LIKE = [[0,6,0,1],[0,5,2,1],[0,4,4,1],[0,3,6,1],[0,3,6,2],[0,2,8,2],[0,2,8,3],[0,1,10,3],[0,1,10,4],[0,1,10,5],[0,1,10,6],\
[0,6,0,2],[0,5,2,2],[0,4,4,2],[0,4,4,3],[0,3,6,3],[0,3,6,4],[0,2,8,4],[0,2,8,5],[0,2,8,6],[0,2,8,7]]

def classify_voronoi_index(list_of_voronoi_index):
	"""
	this function classify a list of voronoi index into a list of
	ico, ico-like, GUMs
	"""
	list_of_voronoi_class = []
	for x in list_of_voronoi_index:
		if len(x) < 6:
			raise Exception("can not classify voronoi index vector whose length is less than 6")
		else:
			truncated_x = x[2:6]
		
		if truncated_x in ICO:
			#list_of_voronoi_class.append('ico')
			list_of_voronoi_class.append(0)
		elif truncated_x in ICO_LIKE:
			#list_of_voronoi_class.append('ico_like')
			list_of_voronoi_class.append(1)
		else:
			#list_of_voronoi_class.append('GUM')
			list_of_voronoi_class.append(2)
	return list_of_voronoi_class
	
def scatter3d(path_to_image, x,y,z,cs, colorsMap='jet'):
    cm = plt.get_cmap(colorsMap)
    cNorm = matplotlib.colors.Normalize(vmin=min(cs), vmax=max(cs))
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    fig = plt.figure()
    ax = Axes3D(fig)
    # view the 3D plot in x-y plane
    ax.view_init(azim=0, elev=90)
    # 2D projection whose z =0 with zdir is z
    ax.scatter(x, y, c=scalarMap.to_rgba(cs))
    scalarMap.set_array(cs)
    fig.colorbar(scalarMap)
    plt.savefig(path_to_image,dpi=600)
    plt.close()
