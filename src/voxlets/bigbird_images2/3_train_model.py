'''
train the model dammit
'''
import numpy as np
import cPickle as pickle
import scipy.io
import sys, os
sys.path.append(os.path.expanduser('~/projects/shape_sharing/src/'))
from sklearn.ensemble import RandomForestClassifier

from common import paths

"Parameters"
max_data_in_subsample = 500000
number_trees = 20
if paths.host_name != 'troll':
    small_sample = True
else:
    small_sample = False

max_depth = 12
if small_sample: print "WARNING: Just computing on a small sample"

####################################################################
print "Loading the dictionary"
km = pickle.load(open(paths.voxlet_dict_path_tsdf, 'rb'))


####################################################################
print "Loading in all the data..."
features = []
all_idxs = []
for count, modelname in enumerate(paths.train_names):

    # loading the data
    loadpath = paths.bigbird_training_data_mat_tsdf % modelname
    print "Loading from " + loadpath

    D = scipy.io.loadmat(loadpath)

    features.append(D['features'])
    
    print "Assigning model shoeboxes to clusters"
    sbox_dim = D['shoeboxes'].shape[2]
    sboxes = D['shoeboxes'].astype(np.float32).reshape((-1, sbox_dim))
    idx_assign = km.predict(sboxes)

    all_idxs.append(idx_assign)


    if count > 2 and small_sample:
        print "SMALL SAMPLE: Stopping"
        break

np_all_idxs = np.hstack(all_idxs).astype(np.uint16)

####################################################################
print "Now training the forest"
np_features = np.array(features).reshape((-1, 56)).astype(np.float16)
to_remove = np.any(np.isnan(np_features), axis=1)
np_features = np_features[~to_remove, :]
np_all_idxs = np_all_idxs[~to_remove]
#np_features[np.isnan(np_features)] = 

print "Idx assign has shape " + str(np_all_idxs.shape)

if max_data_in_subsample > np_features.shape[0]:
    print "Using all data..."
    np_features_subset = np_features
    np_all_idxs_subset = np_all_idxs
else:
    print "Subsampling data..."
    to_use_for_clustering = np.random.randint(0, np_features.shape[0], size=(max_data_in_subsample))
    np_features_subset = np_features[to_use_for_clustering, :]
    np_all_idxs_subset = np_all_idxs[to_use_for_clustering]

print "Features shape before subsampling :" + str(np_features.shape)
print "Features shape after subsampling :" + str(np_features_subset.shape)
print "Idxs shape after subsampling :" + str(np_all_idxs.shape)
print "Idxs shape after subsampling :" + str(np_all_idxs_subset.shape)

forest = RandomForestClassifier(n_estimators=number_trees, criterion="entropy", oob_score=True, max_depth=max_depth, n_jobs=8)
forest.fit(np_features_subset, np_all_idxs_subset)

print "Done training, now saving"
pickle.dump(forest, open(paths.voxlet_model_tsdf_path, 'wb'))

