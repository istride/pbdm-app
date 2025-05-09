import pandas as pd

def create_pbdm_data(client, odk_form_id):
    form_id = get_most_recent_by_org_name(client, odk_form_id)

    (
        repro,
        repro_scalars_var,
        repro_scalar_constants,
        dynamics_repeat,
        dynamics_scalars_var,
        dynamics_scalar_constants,
        mortality_repeat,
        mortality_scalars_var,
        mortality_scalar_constants,
    ) = get_submission_tables(client)

    data = {}
    data["org_name"], data["repro"], data["diapause"] = repro_data(
        form_id, repro, repro_scalars_var, repro_scalar_constants
    )
    data["dynamics"] = dynamics_data(
        form_id, dynamics_repeat, dynamics_scalars_var, dynamics_scalar_constants
    )
    data["mortality"] = mortality_data(
        form_id, mortality_repeat, mortality_scalars_var, mortality_scalar_constants
    )

    return data

def get_table(client, default={}, **kwargs):
    try:
        return client.submissions.get_table(**kwargs)
    except:
        return default
    
def get_most_recent_by_org_name(client, org_name):
    submissions = get_table(client, table_name="Submissions")
    subs_df = pd.json_normalize(data=submissions["value"], sep="/")
    row_id = next(iter(subs_df[subs_df["org_name"] == org_name].sort_values("__system/submissionDate", ascending=False)["__id"]))
    return row_id
    
def get_org_names(client):
    submissions = get_table(client, table_name="Submissions")
    org_names = pd.json_normalize(data=submissions["value"], sep="/")["org_name"]
    return set(org_names)


def bdf_params(row, address):
    return (
        list(map(float, str(x).split(","))) if pd.notna(x := row.get(address)) else []
    )


def get_submission_tables(client):
    repro = pd.json_normalize(
        data=get_table(client, table_name="Submissions").get("value", {}), sep="/"
    )
    dynamics_repeat = pd.json_normalize(
        data=get_table(
            client, table_name="Submissions.dynamics.substage_dynamics_repeat"
        ).get("value", {}),
        sep="/",
    )
    dynamics_scalars_var = pd.json_normalize(
        data=get_table(
            client,
            table_name="Submissions.dynamics.substage_dynamics_repeat.substage_dynamics.substage_dynamics_scalars.substage_dynamics_scalars_var",
        ).get("value", {}),
        sep="/",
    )
    dynamics_scalar_constants = pd.json_normalize(
        data=get_table(
            client,
            table_name="Submissions.dynamics.substage_dynamics_repeat.substage_dynamics.substage_dynamics_scalars.substage_dynamics_scalar_constants_group.substage_dynamics_scalar_constants",
        ).get("value", {}),
        sep="/",
    )
    mortality_repeat = pd.json_normalize(
        data=get_table(
            client, table_name="Submissions.mortality.substage_mortality_repeat"
        ).get("value", {}),
        sep="/",
    )
    mortality_scalars_var = pd.json_normalize(
        data=get_table(
            client,
            table_name="Submissions.mortality.substage_mortality_repeat.substage_mortality.substage_mortality_scalars.substage_mortality_scalars_var",
        ).get("value", {}),
        sep="/",
    )
    mortality_scalar_constants = pd.json_normalize(
        data=get_table(
            client,
            table_name="Submissions.mortality.substage_mortality_repeat.substage_mortality.substage_mortality_scalars.substage_mortality_scalar_constants_group.substage_mortality_scalar_constants",
        ).get("value", {}),
        sep="/",
    )
    repro_scalar_constants = pd.json_normalize(
        data=get_table(
            client,
            table_name="Submissions.org_reproduction.org_reproduction_scalars.org_reproduction_scalar_constants_group.org_reproduction_scalar_constants",
        ).get("value", {}),
        sep="/",
    )
    repro_scalars_var = pd.json_normalize(
        data=get_table(
            client,
            table_name="Submissions.org_reproduction.org_reproduction_scalars.org_reproduction_scalars_var",
        ).get("value", {}),
        sep="/",
    )

    repro.columns = repro.columns.str.replace("org_reproduction_", "").str.replace(
        "org_diapause_", ""
    )
    repro_scalars_var.columns = repro_scalars_var.columns.str.replace(
        "org_reproduction_", ""
    )
    repro_scalar_constants.columns = repro_scalar_constants.columns.str.replace(
        "org_reproduction_", ""
    )
    dynamics_repeat.columns = dynamics_repeat.columns.str.replace(
        "substage_dynamics_", ""
    )
    mortality_repeat.columns = mortality_repeat.columns.str.replace(
        "substage_mortality_", ""
    )
    dynamics_scalars_var.columns = dynamics_scalars_var.columns.str.replace(
        "substage_dynamics_", ""
    )
    dynamics_scalar_constants.columns = dynamics_scalar_constants.columns.str.replace(
        "substage_dynamics_", ""
    )
    mortality_scalars_var.columns = mortality_scalars_var.columns.str.replace(
        "substage_mortality_", ""
    )
    mortality_scalar_constants.columns = mortality_scalar_constants.columns.str.replace(
        "substage_mortality_", ""
    )

    return (
        repro,
        repro_scalars_var,
        repro_scalar_constants,
        dynamics_repeat,
        dynamics_scalars_var,
        dynamics_scalar_constants,
        mortality_repeat,
        mortality_scalars_var,
        mortality_scalar_constants,
    )


def repro_data(form_id, repro, repro_scalars_var, repro_scalar_constants):
    data = {}

    row_filter = repro[repro["__id"] == form_id]

    for _, row in row_filter.iterrows():
        row_id = row["__id"]

        vars_filter = repro_scalars_var[repro_scalars_var["__Submissions-id"] == row_id]
        scalar_vars_list = [
            {
                "current_var_id": r.get("scalar_current_var_id", ""),
                "bdf": r.get("scalar_bdf", ""),
                "bdf_parameters": bdf_params(r, "scalar_bdf_parameters"),
            }
            for _, r in vars_filter.iterrows()
        ]

        constants_filter = repro_scalar_constants[
            repro_scalar_constants["__Submissions-id"] == row_id
        ]
        scalar_constants_list = [
            {
                "scalar_constant_name": r.get("scalar_constant_name", ""),
                "scalar_constant_value": r.get("scalar_constant_value", ""),
            }
            for _, r in constants_filter.iterrows()
        ]

        org_name = str(row["org_name"])

        repro_data = {
            "constant_bool": str(row["org_reproduction/constant_bool"]) == "yes",
            "constant": (
                float(row["org_reproduction/constant"])
                if pd.notna(row["org_reproduction/constant"])
                else None
            ),
            "function_var": row.get("org_reproduction/function/function_var"),
            "function_bdf": row.get("org_reproduction/function/function_bdf"),
            "function_bdf_parameters": bdf_params(
                row, "org_reproduction/function/function_bdf_parameters"
            ),
            "scalars_bool": str(
                row.get("org_reproduction/function/scalars_bool")
            ).lower()
            == "yes",
            "scalar_constants_bool": str(
                row.get("org_reproduction/scalars/scalar_constants_bool")
            ).lower()
            == "yes",
            "scalar_constants": scalar_constants_list,
            "scalar_vars": scalar_vars_list,
        }

        diap_data = {
            "bool": str(row["diapause/bool"]) == "yes",
            "prev_stage": str(row.get("diapause/function/prev_stage")),
            "next_stage": str(row.get("diapause/function/next_stage")),
            "entry_function_var": str(
                row.get("diapause/function/entry_function/entry_function_var")
            ),
            "entry_function_bdf": str(
                row.get("diapause/function/entry_function/entry_function_bdf")
            ),
            "entry_function_bdf_parameters": bdf_params(
                row, "diapause/function/entry_function/entry_function_bdf_parameters"
            ),
            "exit_function_var": str(
                row.get("diapause/function/exit_function/exit_function_var")
            ),
            "exit_function_bdf": str(
                row.get("diapause/function/exit_function/exit_function_bdf")
            ),
            "exit_function_bdf_parameters": bdf_params(
                row, "diapause/function/exit_function/exit_function_bdf_parameters"
            ),
        }

        return org_name, repro_data, diap_data


def dynamics_data(
    form_id, dynamics_repeat, dynamics_scalars_var, dynamics_scalar_constants
):
    filter_substage = dynamics_repeat[dynamics_repeat["__Submissions-id"] == form_id]

    dynamics = {}

    for _, row in filter_substage.iterrows():

        row_id = row["__id"]

        vars_filter = dynamics_scalars_var[
            dynamics_scalars_var["__Submissions-dynamics-repeat-id"] == row_id
        ]
        scalar_vars_list = [
            {
                "current_var_id": r.get("scalar_current_var_id", ""),
                "bdf": r.get("scalar_bdf", ""),
                "bdf_parameters": bdf_params(r, "scalar_bdf_parameters"),
            }
            for _, r in vars_filter.iterrows()
        ]

        constants_filter = dynamics_scalar_constants[
            dynamics_scalar_constants["__Submissions-dynamics-repeat-id"] == row_id
        ]
        scalar_constants_list = [
            {
                "scalar_constant_name": r.get("scalar_constant_name", ""),
                "scalar_constant_value": (
                    float(x) if pd.notna(x := r.get("scalar_constant_value")) else 0
                ),
            }
            for _, r in constants_filter.iterrows()
        ]

        dyn_data = {
            "inherit": str(row.get("inherit_unique")) == "inherit",
            "inherit_from": str(row.get("inherit_from", "")),
            "Del": float(x) if pd.notna(x := row.get("substage_dynamics/del")) else 0,
            "variance": (
                float(x) if pd.notna(x := row.get("substage_dynamics/var")) else 0
            ),
            "constant_bool": str(row["substage_dynamics/constant_bool"]) == "yes",
            "constant": (
                float(row["substage_dynamics/constant"])
                if pd.notna(row["substage_dynamics/constant"])
                else None
            ),
            "function_var": row.get("substage_dynamics/function/function_var"),
            "function_bdf": row.get("substage_dynamics/function/function_bdf"),
            "function_bdf_parameters": bdf_params(
                row, "substage_dynamics/function/function_bdf_parameters"
            ),
            "scalars_bool": str(
                row.get("substage_dynamics/function/scalars_bool")
            ).lower()
            == "yes",
            "scalar_constants_bool": str(
                row.get("substage_dynamics/scalars/scalar_constants_bool")
            ).lower()
            == "yes",
            "scalar_constants": scalar_constants_list,
            "scalar_vars": scalar_vars_list,
        }

        name = row["current_name"].lower()

        dynamics[name] = dyn_data

    return dynamics


def mortality_data(
    form_id, mortality_repeat, mortality_scalars_var, mortality_scalar_constants
):
    filter_substage = mortality_repeat[mortality_repeat["__Submissions-id"] == form_id]

    mortality = {}

    for _, row in filter_substage.iterrows():

        row_id = row["__id"]

        vars_filter = mortality_scalars_var[
            mortality_scalars_var["__Submissions-mortality-repeat-id"] == row_id
        ]
        scalar_vars_list = [
            {
                "current_var_id": r.get("scalar_current_var_id", ""),
                "bdf": r.get("scalar_bdf", ""),
                "bdf_parameters": bdf_params(r, "scalar_bdf_parameters"),
            }
            for _, r in vars_filter.iterrows()
        ]

        constants_filter = mortality_scalar_constants[
            mortality_scalar_constants["__Submissions-mortality-repeat-id"] == row_id
        ]
        scalar_constants_list = [
            {
                "scalar_constant_name": r.get("scalar_constant_name", ""),
                "scalar_constant_value": (
                    float(x) if pd.notna(x := r.get("scalar_constant_value")) else 0
                ),
            }
            for _, r in constants_filter.iterrows()
        ]

        mort_data = {
            "inherit": str(row.get("inherit_unique")) == "inherit",
            "inherit_from": str(row.get("inherit_from", "")),
            "constant_bool": str(row["substage_mortality/constant_bool"]) == "yes",
            "constant": (
                float(row["substage_mortality/constant"])
                if pd.notna(row["substage_mortality/constant"])
                else None
            ),
            "function_var": row.get("substage_mortality/function/function_var"),
            "function_bdf": row.get("substage_mortality/function/function_bdf"),
            "function_bdf_parameters": bdf_params(
                row, "substage_mortality/function/function_bdf_parameters"
            ),
            "scalars_bool": str(
                row.get("substage_mortality/function/scalars_bool")
            ).lower()
            == "yes",
            "scalar_constants_bool": str(
                row.get("substage_mortality/scalars/scalar_constants_bool")
            ).lower()
            == "yes",
            "scalar_constants": scalar_constants_list,
            "scalar_vars": scalar_vars_list,
            "density_bool": str(row.get("substage_mortality/density_bool")) == "yes",
            "density_function_bdf": str(
                row.get("substage_mortality/density_function/density_function_bdf")
            ),
            "density_function_bdf_parameters": bdf_params(
                row,
                "substage_mortality/density_function/density_function_bdf_parameters",
            ),
        }

        name = row["current_name"].lower()

        mortality[name] = mort_data

    return mortality



"""
import os
from pyodk.client import Client

BASE_DIR = os.path.dirname(os.path.abspath(""))
CONFIG_DIR = os.path.join(BASE_DIR, "pbdm-flask-app", "pyodk_config.toml")
# Authenticate with ODK Central
client = Client(config_path=CONFIG_DIR)
client.projects.default_project_id = 10
client.forms.default_form_id = "pbdm_bdf"
client.submissions.default_form_id = "pbdm_bdf"
"""
#data = create_pbdm_data(client, "Organism")

#print(data)
#print(create_pbdm_data(client, 0))


# Get org name from subs_df
# Store org name
# Get most recent submission for org name