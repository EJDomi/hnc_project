#!/usr/bin/env python

model_config = {
                "model_name": 'ClinicalGatedGCN',
                "extractor_name": 'ResNet',
                "dataset_name": 'HNSCC',
                "external_dataset_name": 'UTSW',
                "clinical_data": 'clinical_features.pkl',
                "data_type": 'image',
                "scaling_type": 'MinMax',
                "with_edge_attr": False,
                "cross_val": True,
                "nested_cross_val": False,
                "edge_dim": 1,
                # v1 has 29, v2 has 32
                "n_clinical": 32,
                "use_clinical": False, 
	        "batch_size": 12,
	        "n_epochs": 100,
                "seed": 42,
                "n_classes": 1,
                "n_extracted_features": 2048,
                "n_hidden_channels": 64,
                "n_channels": 1,
                #"learning_rate": 0.01,
	        "dropout": 0.0,
	        "ext_dropout": 0.0,
                "l2_reg": 0,
                "learning_rate": 0.1,
                "lr_sched": True,
                "lr_factor": 0.5,
                "lr_patience": 10,
                "lr_mode": 'max',
                "log_dir": None,
                "augment": False,
                "augments": ['rotation'],
                "n_rotations": 10,
                "transfer": None,
                "clinical_mean": {'Win42': [[58.1292, 68.8017],
                                         [58.4310, 68.6708],
                                         [58.1092, 68.4468],
                                         [57.7479, 68.5578],
                                         [57.7699, 68.7778]] 
                                 },
                "clinical_std": {'Win42': [[9.1257, 2.2914],
                                        [8.9034, 2.3877],
                                        [8.8726, 2.4658],
                                        [9.0592, 2.3217],
                                        [9.3560, 2.1930]]
                                },
               "num_deep_layers": 28,
               "positive_increase": 5,
               "radiomics_mean": '../../data/HNSCC/radiomics_mean.pt',
               "radiomics_std": '../../data/HNSCC/radiomics_std.pt',
               }         

