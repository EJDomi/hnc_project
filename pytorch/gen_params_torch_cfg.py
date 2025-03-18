#!/usr/bin/env python

model_config = {
                "gpu_device": [0],
                "dataset_name": 'RADCURE',
                "external_dataset_name": 'UTSW_HNC',
                "use_GTVp_only": False,
                "no_GTVp_pickle": 'patients_with_no_gtvp.pkl',
                "challenge": True,
                "preset_folds": False,
                "preset_fold_file": 'preset_folds_061424.pkl',
                "clinical_data": 'clinical_features.pkl',
                "data_path": '../../data/RADCURE',
                "patch_dir": 'Nii_111_80_80_80_Crop',
                "radiomics_dir": 'radiomics',
                "use_radiomics": False,
                "edge_file": 'edges_radcure_053024.pkl',
                "locations_file": 'centered_locations_radcure_060424.pkl',
                "remove_censored": False,
                "data_version": 'initial_rot10_30_balance_v1',
                "log_dir": 'log_dir_temp',
                "data_type": 'image',
                "scaling_type": 'MinMax',
                "with_edge_attr": False,
                "cross_val": True,
                "nested_cross_val": False,
                "edge_dim": 1,
                "reverse_edges": False,
                "complete_graph": False,
                "undirected_graph": False,
                "star_graph": False,
                # v1 has 29, v2 has 32
                "n_clinical": 32,
                "n_radiomics": 1316,
                "n_embeddings": 1408,
                "use_clinical": False, 
	        "batch_size": 12,
	        "n_epochs": 100,
                "seed": 42,
                "n_classes": 1,
                "multi_label": False,
                "class_weight": 1.,
                "model_name": 'ClinicalGatedGCN',
                "extractor_name": 'ResNet',
                #"n_extracted_features": 64,
                "extractor_channels": 64,
                "n_hidden_channels": 64,
                "n_in_channels": 1,
                #"learning_rate": 0.01,
	        "dropout": 0.0,
	        "ext_dropout": 0.0,
                "save_top_k": 1,
                "l2_reg": 0,
                "learning_rate": 0.1,
                "lr_sched": True,
                "lr_factor": 0.1,
                "lr_patience": 10,
                "lr_mode": 'min',
                "log_dir": None,
                "augment": False,
                "augments": ['rotation'],
                "transfer": None,
                "n_rotations": 10,
               "num_deep_layers": 28,
               "positive_increase": 5,
               "balance_classes": False,
               "true_balance_classes": False,
               "class_weights": 20.,
               "graph_pooling": False,
                "max_nodes": { 'HNSCC': 15,
                             },
                "clinical_means": {
                                  'RADCURE' : [[62.12, 26.9, 66.4, 32.9],
                                               [61.9, 26.4, 66.5, 33.1],
                                               [62.4, 26.5, 66.3, 32.8],
                                               [62.5, 26.7, 66.4, 32.9],
                                               [62.0, 26.7, 66.3, 32.8]]
                                 },
                "clinical_stds": {
                                 'RADCURE': [[11.9, 24.9, 5.92, 5.48],
                                             [11.9, 25.3, 5.81, 5.39],
                                             [11.9, 24.9, 5.94, 5.51],
                                             [11.9, 25.2, 5.86, 5.45],
                                             [11.9, 25.0, 5.94, 5.52]]
                                },
               "radiomics_mean": './radiomics_means.pkl',
               "radiomics_std": './radiomics_stds.pkl',
               "store_radiomics": True,
               "store_embeddings": True,
               "use_embeddings": False,
               "embedding_file": 'radcure_ln_ct_embeddings_redo_v2.pkl',
               "cut_on_ngtvs": False,
               "regression": False,
               "time_bins": 8,
               "use_images": False
               }         

