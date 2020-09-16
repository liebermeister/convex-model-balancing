% -------------------------------------------------------------------
% Model balancing demo script
%
% o the model is read from an SBML or SBtab file
% o artificial data are generated
% o model balancing is performed
% -------------------------------------------------------------------


% -------------------------------------------------------------
% Define model and initial concentration guess
% -------------------------------------------------------------

% -------------------------------------------------------------
% Small test model (network structure from SBML or SBtab file)
%
% Network structure
% - \   /
%     -
% _ /   \
% -------------------------------------------------------------


model        = 'double_branch_model';
run          = 'test';
result_dir   = tempdir;
% Note that the network file can be either SBML or SBtab
network_file = [cmb_resourcedir '/models/double_branch_model/sbml/double_branch_model.xml'];
layout_file  = [cmb_resourcedir '/models/double_branch_model/sbtab/multi/double_branch_model_POSITION.tsv'];
c_init       = [10,1,1,1,1,1,0.01]'; 
ns           = 6;

filenames = cmb_filenames(model, run, result_dir, network_file);


% -------------------------------------------------------------
% E. coli CCM model (network structure from SBML file)
% To use this example model, uncomment the following lines
% (calculation time about 30 minutes)
% -------------------------------------------------------------

% model        = 'e_coli_artificial';  
% run          = 'no_noise_with_noisefree_kinetic_data';
% result_dir   = tempdir;
% network_file = [cmb_resourcedir '/data/data-organisms/escherichia_coli/network/ecoli_ccm_ProteinComposition_Network.xml'];
% layout_file  = [];
% c_init       = e_coli_c_init(model,cmb_default_options);
% ns           = 4;


% -------------------------------------------------------------
% Set options
% -------------------------------------------------------------

cmb_options                        = cmb_default_options;
cmb_options.run                    = run;
cmb_options.ns                     = ns;
cmb_options.prior_variant          = 'broad_prior';
cmb_options.use_kinetic_data       = 'all';
cmb_options.use_artificial_noise   = 0;
cmb_options.use_kinetic_data_noise = 0;
cmb_options.initial_values_variant = 'average_sample';
cmb_options.show_graphics          = 1;
cmb_options.verbose                = run;


% -----------------------------------------------
% Prepare data structures: load SBML network model and 
% generate "true" kinetic model, priors, and artificial data
% -----------------------------------------------

[network, bounds, prior, q_info, data, true, kinetic_data, state_data] = cmb_model_artificial_data(network_file, cmb_options, c_init, layout_file);


% -----------------------------------------------
% Run model balancing and save results to files 
% -----------------------------------------------

convex_model_balancing(filenames, cmb_options, network, q_info, prior, bounds, data, true);