"""
A module for I/O operations related to model balancing.

"""

import json
from typing import Dict, List, Union

import numpy as np
import pandas as pd
from sbtab import SBtab

from . import Q_

JSON_NAME_MAPPINGS = {
    "Keq": ("kinetic_constants", "Keq"),
    "Km": ("kinetic_constants", "KM"),
    "Ka": ("kinetic_constants", "KA"),
    "Ki": ("kinetic_constants", "KI"),
    "kcatf": ("kinetic_constants", "Kcatf"),
    "kcatr": ("kinetic_constants", "Kcatr"),
    "conc_met": ("metabolite_concentrations",),
    "conc_enz": ("enzyme_concentrations",),
}  # mapping from the variable names in python to the location in the JSON


def standardize_input_matrix(x: Union[List[float], np.array], unit: str) -> Q_:
    """Create a 2D Numpy array of Quantities.

    If the input is only 1D, make sure it becomes a 2D array with a single
    column. This is important because we always assume that all our inputs are
    2D.
    """
    if not x:
        return Q_(x, unit)
    elif type(x) == list:
        return Q_(x, unit).reshape(len(x), -1)
    else:
        return Q_(x, unit).reshape(x.shape[0], -1)


def read_arguments_json(
    json_fname: str,
) -> Dict[str, np.array]:
    """Read the list of model balancing arguments from a JSON.

    See our page about the :ref:`JSON specification sheet <json>`.
    """
    with open(json_fname, "rt") as fp:
        data = json.load(fp)

    keq_standard_concentration = Q_(data["standard_concentration"])

    args = {}
    args["S"] = np.array(data["network"]["stoichiometric_matrix"])
    args["A_act"] = np.array(data["network"]["activation_matrix"])
    args["A_inh"] = np.array(data["network"]["inhibition_matrix"])
    args["fluxes"] = standardize_input_matrix(
        data["reaction_fluxes"]["data"]["mean"], data["reaction_fluxes"]["unit"]
    )

    # Read the kinetic parameters that have 'normal' units:
    for p in JSON_NAME_MAPPINGS.keys():
        # in the JSON, parameter names have slightly different casing, so we
        # use a dictionary for converting between the conventions.
        p_json = data
        for k in JSON_NAME_MAPPINGS[p]:
            p_json = p_json[k]

        unit = p_json["unit"]

        if "cov_ln" in p_json["combined"]:
            args[f"{p}_ln_cov"] = np.array(p_json["combined"]["cov_ln"])
        elif "geom_std" in p_json["combined"]:
            args[f"{p}_ln_cov"] = (
                np.diag(np.log(np.array(p_json["combined"]["geom_std"]).T.flatten()))
                ** 2.0
            )
        else:
            raise KeyError(
                f"Cannot find neither `cov_ln` nor `geom_std` in the `combined` field of {p}"
            )

        if unit == "depends on reaction stoichiometry":
            # For the equilibrium constants, which are unitless but if the standard
            # concentration is not 1M, we need to adjust their values based on what
            # it is in the JSON file.
            A = np.diag(
                np.power(keq_standard_concentration.m_as("M"), args["S"].sum(axis=0))
            )
            args["Keq_gmean"] = A @ Q_(p_json["combined"]["geom_mean"], "")
            args[f"{p}_lower_bound"] = A @ Q_(p_json["bounds"]["min"], "")
            args[f"{p}_upper_bound"] = A @ Q_(p_json["bounds"]["max"], "")
        else:
            args[f"{p}_gmean"] = Q_(
                p_json["combined"]["geom_mean"],
                p_json["unit"],
            )
            args[f"{p}_lower_bound"] = Q_(
                p_json["bounds"]["min"],
                p_json["unit"],
            )
            args[f"{p}_upper_bound"] = Q_(
                p_json["bounds"]["max"],
                p_json["unit"],
            )

    args["metabolite_names"] = data["network"]["metabolite_names"]
    args["reaction_names"] = data["network"]["reaction_names"]
    args["state_names"] = data["state_names"]
    args["rate_law"] = "CM"
    return args


def to_state_sbtab(
    v,
    c,
    e,
    delta_g,
    metabolite_names,
    reaction_names,
    state_names,
) -> SBtab.SBtabDocument:
    """Create a state SBtab.

    The state SBtab contains the values of the state-dependent variables,
    i.e. flux, concentrations of metabolites, concentrations of enzymes,
    and the ΔG' values.
    """

    state_sbtabdoc = SBtab.SBtabDocument(name="MB result")
    flux_df = pd.DataFrame(v.m_as("mM/s"), columns=state_names)
    flux_df.insert(0, "!QuantityType", "rate of reaction")
    flux_df.insert(1, "!Reaction", reaction_names)
    flux_sbtab = SBtab.SBtabTable.from_data_frame(
        flux_df.astype(str),
        table_id="Flux",
        table_name="Metabolic fluxes",
        table_type="QuantityMatrix",
        unit="mM/s",
    )
    state_sbtabdoc.add_sbtab(flux_sbtab)

    conc_met_df = pd.DataFrame(c.m_as("mM"), columns=state_names)
    conc_met_df.insert(0, "!QuantityType", "concentration")
    conc_met_df.insert(1, "!Compound", metabolite_names)
    conc_met_sbtab = SBtab.SBtabTable.from_data_frame(
        conc_met_df.astype(str),
        table_id="MetaboliteConcentration",
        table_name="Metabolite concentration",
        table_type="QuantityMatrix",
        unit="mM",
    )
    state_sbtabdoc.add_sbtab(conc_met_sbtab)

    conc_enz_df = pd.DataFrame(e.m_as("mM"), columns=state_names)
    conc_enz_df.insert(0, "!QuantityType", "concentration of enzyme")
    conc_enz_df.insert(1, "!Reaction", reaction_names)
    conc_enz_sbtab = SBtab.SBtabTable.from_data_frame(
        conc_enz_df.astype(str),
        table_id="EnzymeConcentration",
        table_name="Enzyme concentration",
        table_type="QuantityMatrix",
        unit="mM",
    )
    state_sbtabdoc.add_sbtab(conc_enz_sbtab)

    gibbs_energy_df = pd.DataFrame(delta_g.m_as("kJ/mol"), columns=state_names)
    gibbs_energy_df.insert(0, "!QuantityType", "Gibbs energy of reaction")
    gibbs_energy_df.insert(1, "!Reaction", reaction_names)
    gibbs_energy_sbtab = SBtab.SBtabTable.from_data_frame(
        gibbs_energy_df.astype(str),
        table_id="ReactionGibbsFreeEnergy",
        table_name="Gibbs free energies of reaction",
        table_type="QuantityMatrix",
        unit="kJ/mol",
    )
    state_sbtabdoc.add_sbtab(gibbs_energy_sbtab)
    return state_sbtabdoc


def to_model_sbtab(
    kcatf,
    kcatr,
    Keq,
    Km,
    Ka,
    Ki,
    S,
    A_act,
    A_inh,
    metabolite_names,
    reaction_names,
    state_names,
) -> SBtab.SBtabDocument:
    """Create a model SBtab.

    The model SBtab contains the values of the state-independent variables,
    i.e. kcatf, kcatr, Km, Ka, and Ki.
    """

    model_sbtabdoc = SBtab.SBtabDocument(name="MB result")

    parameter_data = []
    parameter_data += [
        ("equilibrium constant", rxn, "", value, "dimensionless")
        for rxn, value in zip(reaction_names, Keq.m_as(""))
    ]
    parameter_data += [
        ("catalytic rate constant geometric mean", rxn, "", value.m_as("1/s"), "1/s")
        for rxn, value in zip(reaction_names, (kcatf * kcatr) ** (0.5))
    ]
    parameter_data += [
        ("forward catalytic rate constant", rxn, "", value.m_as("1/s"), "1/s")
        for rxn, value in zip(reaction_names, kcatf)
    ]
    parameter_data += [
        ("reverse catalytic rate constant", rxn, "", value.m_as("1/s"), "1/s")
        for rxn, value in zip(reaction_names, kcatr)
    ]
    for j, rxn in enumerate(reaction_names):
        for i, met in enumerate(metabolite_names):
            if S[i, j] != 0:
                parameter_data += [
                    ("Michaelis constant", rxn, met, Km[i, j].m_as("mM"), "mM")
                ]
            if A_act[i, j] != 0:
                parameter_data += [
                    ("Activation constant", rxn, met, Ka[i, j].m_as("mM"), "mM")
                ]
            if A_inh[i, j] != 0:
                parameter_data += [
                    ("Inhibition constant", rxn, met, Ki[i, j].m_as("mM"), "mM")
                ]

    parameter_df = pd.DataFrame(
        data=parameter_data,
        columns=["!QuantityType", "!Reaction", "!Compound", "!Mode", "!Unit"],
    ).sort_values("!QuantityType")

    parameter_sbtab = SBtab.SBtabTable.from_data_frame(
        parameter_df.astype(str),
        table_id="Parameter",
        table_name="Parameter",
        table_type="Quantity",
        unit="",
    )
    parameter_sbtab.change_attribute("StandardConcentration", "M")
    model_sbtabdoc.add_sbtab(parameter_sbtab)

    return model_sbtabdoc


__all__ = [
    "standardize_input_matrix",
    "read_arguments_json",
    "to_state_sbtab",
    "to_model_sbtab",
]
