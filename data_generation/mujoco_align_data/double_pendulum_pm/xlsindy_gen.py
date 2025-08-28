"""
this script is used by mujoco_align.py in order to generate catalog of function and reference lagrangian for the xl_sindy algorithn

it can be used as a template for the xlsindy_back_script argument of the mujoco_align.py script and should strictly follow the input output format
"""

import xlsindy
import numpy as np
import sympy as sp

from typing import List
import os 


import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from text_utils import replace_placeholders

mujoco_angle_offset = np.pi


def xlsindy_component(
    mode: str = "xlsindy", random_seed: List[int] = [12], sindy_catalog_len: int = 93, damping_coefficients: List[float] = [-1.0, -1.4]
):  # Name of this function should not be changed
    """
    This function is used to generate backbone of the xl_sindy algorithm

    this version can be used as a template for the xlsindy_back_script argument of the mujoco_align.py script and should strictly follow the input output format.
    name of the function should not be changed

    Returns:
        np.ndarray: matrix of shape (4, n) containing symbolic expression.
        List[sympy.Expr]: List of combined functions.
        Dict: extra_info dictionnary containing extra information about the system
    """

    ## Import the environment xml file and perform the necessary transformations

    xml_file = os.path.join(os.path.dirname(__file__), "environment.xml")

    with open(xml_file, "r") as file:
        xml_content = file.read()
    # Replace the damping coefficients in the xml content
    xml_content = replace_placeholders(
        xml_content,
        {
            "DAMPING_1": str(-damping_coefficients[0]),
            "DAMPING_2": str(-damping_coefficients[1]),
        },
    )

    time_sym = sp.symbols("t")

    num_coordinates = 2

    symbols_matrix = xlsindy.symbolic_util.generate_symbolic_matrix(
        num_coordinates, time_sym
    )

    link1_length = 1.0
    link2_length = 1.0
    mass1 = 0.8
    mass2 = 0.4


    friction_forces = np.array(
        [
            [damping_coefficients[0] + damping_coefficients[1], -damping_coefficients[1]],
            [-damping_coefficients[1], damping_coefficients[1]],
        ]
    )
    friction_function = np.array(
        [[symbols_matrix[2, x] for x in range(num_coordinates)]]
    )
    # Assign ideal model variables
    theta1 = symbols_matrix[1, 0]
    theta1_d = symbols_matrix[2, 0]
    theta1_dd = symbols_matrix[3, 0]

    theta2 = symbols_matrix[1, 1]
    theta2_d = symbols_matrix[2, 1]
    theta2_dd = symbols_matrix[3, 1]

    m1, l1, m2, l2, g = sp.symbols("m1 l1 m2 l2 g")
    total_length = link1_length + link2_length
    substitutions = {
        "g": 9.81,
        "l1": link1_length,
        "m1": mass1,
        "l2": link2_length,
        "m2": mass2,
    }

    # Lagrangian (L)
    Lagrangian = (
        0.5 * (m1 + m2) * l1**2 * theta1_d**2
        + 0.5 * m2 * l2**2 * theta2_d**2
        + m2 * l1 * l2 * theta1_d * theta2_d * sp.cos(theta1 - theta2)
        + (m1 + m2) * g * l1 * sp.cos(theta1)
        + m2 * g * l2 * sp.cos(theta2)
    )

    if mode == "xlsindy":

        # Create the catalog (Mandatory part)
        function_catalog_1 = [lambda x: symbols_matrix[2, x]]
        function_catalog_2 = [
            lambda x: sp.sin(symbols_matrix[1, x]),
            lambda x: sp.cos(symbols_matrix[1, x]),
        ]

        catalog_part1 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                function_catalog_1, num_coordinates, 2
            )
        )
        catalog_part2 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                function_catalog_2, num_coordinates, 2
            )
        )
        cross_catalog = np.outer(catalog_part2, catalog_part1)

        lagrange_catalog = np.concatenate(
            (cross_catalog.flatten(), catalog_part1, catalog_part2)
        ) 

        friction_catalog = (
            friction_function.flatten()
        )  # Contain only \dot{q}_1 \dot{q}_2

        expand_matrix = np.ones((len(friction_catalog), num_coordinates), dtype=int)

        catalog_repartition = xlsindy.catalog.CatalogRepartition(
            [
                xlsindy.catalog_base.ExternalForces(
                    [[1,-2], [2]], symbols_matrix
                ),
                xlsindy.catalog_base.Lagrange(
                    lagrange_catalog, symbols_matrix, time_sym
                ),
                xlsindy.catalog_base.Classical(
                    friction_catalog, expand_matrix
                ),
            ]
        )

        ideal_solution_vector = catalog_repartition.create_solution_vector(
            [
                ([]),
                ([Lagrangian.subs(substitutions)]),
                ([friction_forces]),
            ]
        )

        catalog_len = len(ideal_solution_vector)

    elif mode == "sindy":

        newton_equations = xlsindy.euler_lagrange.newton_from_lagrangian(
            Lagrangian.subs(substitutions), symbols_matrix, time_sym
        )
        newton_system = []

        newton_equations += (friction_function @ friction_forces).flatten()

        # print(newton_equations)

        for i in range(num_coordinates):

            newton_system += [
                xlsindy.symbolic_util.get_additive_equation_term(
                    sp.expand_trig(newton_equations[i])
                )
            ]

        catalog_need, coeff_matrix, binary_matrix = (
            xlsindy.symbolic_util.sindy_create_coefficient_matrices(newton_system)
        )

        # complete the catalog

        function_catalog_0 = [lambda x: symbols_matrix[3, x]]  # \ddot{x}
        function_catalog_1 = [lambda x: symbols_matrix[2, x]]  # \ddot{x}
        function_catalog_2 = [
            lambda x: sp.sin(symbols_matrix[1, x]),
            lambda x: sp.cos(symbols_matrix[1, x]),
        ]

        catalog_part0 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                function_catalog_0, num_coordinates, 1
            )
        )
        catalog_part1 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                function_catalog_1, num_coordinates, 2
            )
        )
        catalog_part2 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                function_catalog_2, num_coordinates, 2
            )
        )

        lagrange_catalog = xlsindy.symbolic_util.cross_catalog(
            catalog_part1, catalog_part2
        )
        lagrange_catalog = xlsindy.symbolic_util.cross_catalog(
            lagrange_catalog, catalog_part0
        )
        # --------------------

        coeff_matrix, binary_matrix, catalog_need = xlsindy.symbolic_util.augment_catalog(
            num_coordinates,
            lagrange_catalog,
            coeff_matrix,
            binary_matrix,
            catalog_need,
            sindy_catalog_len,
            random_seed,
        )

        catalog_repartition = xlsindy.catalog.CatalogRepartition(
            [
                xlsindy.catalog_base.ExternalForces(
                    [[1,-2], [2]], symbols_matrix
                ),
                xlsindy.catalog_base.Classical(
                    catalog_need, binary_matrix
                ),
            ]
        )

        ideal_solution_vector = catalog_repartition.create_solution_vector(
            [
                ([]),
                ([coeff_matrix]),
            ]
        )

        catalog_len = len(ideal_solution_vector)

    # Create the extra_info dictionnary
    extra_info = {
        "lagrangian": Lagrangian,
        "substitutions": substitutions,
        "friction_forces": friction_forces,
        "ideal_solution_vector": ideal_solution_vector,
        "initial_condition": np.array([[np.pi, 0], [np.pi, 0]]),
        "catalog_len": catalog_len,
    }

    return (
        num_coordinates,
        time_sym,
        symbols_matrix,
        catalog_repartition,
        xml_content,
        extra_info,
    )  # extra_info is optionnal and should be set to None if not in use


def mujoco_transform(pos, vel, acc):

    pos = -np.cumsum(pos, axis=1) + mujoco_angle_offset
    vel = -np.cumsum(vel, axis=1)
    acc = -np.cumsum(acc, axis=1)

    return pos, vel, acc

def inverse_mujoco_transform(tpos, tvel, tacc):
    """
    Given outputs of mujoco_transform (tpos, tvel, tacc),
    recover the original pos, vel, acc (all shape (batch, n)).
    """
    # Undo the negated cumsum (and offset for angles)
    S_pos = -(tpos - mujoco_angle_offset)
    S_vel = -tvel
    if tacc is not None:
        S_acc = -tacc

    # invert cumulative sum by taking differences (with zero prepended)
    pos = np.diff(S_pos, axis=1, prepend=np.zeros((S_pos.shape[0],1)))
    vel = np.diff(S_vel, axis=1, prepend=np.zeros((S_vel.shape[0],1)))
    if tacc is not None:
        acc = np.diff(S_acc, axis=1, prepend=np.zeros((S_acc.shape[0],1)))

    if tacc is not None:
        return pos, vel, acc
    else:
        return pos, vel, None