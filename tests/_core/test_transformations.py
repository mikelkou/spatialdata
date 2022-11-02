import numpy as np
import pytest

from spatialdata._core.coordinate_system import Axis, CoordinateSystem
from spatialdata._core.transformations import (
    BaseTransformation,
    Identity,
)

x_axis = Axis(name="x", type="space", unit="micrometer")
y_axis = Axis(name="y", type="space", unit="micrometer")
z_axis = Axis(name="z", type="space", unit="micrometer")
c_axis = Axis(name="c", type="channel")
xy_cs = CoordinateSystem(name="xy", axes=[x_axis, y_axis])
xyz_cs = CoordinateSystem(name="xyz", axes=[x_axis, y_axis, z_axis])
yx_cs = CoordinateSystem(name="yx", axes=[y_axis, x_axis])
zyx_cs = CoordinateSystem(name="zyx", axes=[z_axis, y_axis, x_axis])
cyx_cs = CoordinateSystem(name="cyx", axes=[c_axis, y_axis, x_axis])
czyx_cs = CoordinateSystem(name="czyx", axes=[c_axis, z_axis, y_axis, x_axis])


def _test_transform_points(
    transformation: BaseTransformation,
    original: np.ndarray,
    transformed: np.ndarray,
    input_cs: CoordinateSystem,
    output_cs: CoordinateSystem,
    wrong_output_cs: CoordinateSystem,
    test_affine: bool = True,
    test_inverse: bool = True,
):
    # missing input and output coordinate systems
    with pytest.raises(ValueError):
        assert np.allclose(transformation.transform_points(original), transformed)

    # missing output coordinate system
    transformation.input_coordinate_system = input_cs
    with pytest.raises(ValueError):
        assert np.allclose(transformation.transform_points(original), transformed)

    # wrong output coordinate system
    transformation.output_coordinate_system = wrong_output_cs
    with pytest.raises(ValueError):
        assert np.allclose(transformation.transform_points(original), transformed)

    # wrong points shapes
    transformation.output_coordinate_system = output_cs
    with pytest.raises(ValueError):
        assert np.allclose(transformation.transform_points(original.ravel()), transformed.ravel())
    with pytest.raises(ValueError):
        assert np.allclose(transformation.transform_points(original.transpose()), transformed.transpose())
    with pytest.raises(ValueError):
        assert np.allclose(transformation.transform_points(np.expand_dims(original, 0)), np.expand_dims(transformed, 0))

    # correct
    assert np.allclose(transformation.transform_points(original), transformed)

    if test_affine:
        affine = transformation.to_affine()
        assert np.allclose(affine.transform_points(original), original)

    if test_inverse:
        inverse = transformation.inverse()
        assert np.allclose(inverse.transform_points(transformed), original)

    # test to_dict roundtrip
    assert transformation.to_dict() == BaseTransformation.from_dict(transformation.to_dict()).to_dict()

    # test to_json roundtrip
    assert transformation.to_json() == BaseTransformation.from_json(transformation.to_json()).to_json()


def test_identity():
    _test_transform_points(
        transformation=Identity(),
        original=np.array([[1, 2, 3]]),
        transformed=np.array([[1, 2, 3]]),
        input_cs=xyz_cs,
        output_cs=xyz_cs,
        wrong_output_cs=zyx_cs,
    )

    # t.output_coordinate_system = xy_cs

    # assert np.allclose(
    #     act('{"type": "identity"}', ndim=2),
    #     np.array([[1, 2], [3, 4], [5, 6]], dtype=float),
    # )


#
#
# @pytest.mark.skip()
# def test_map_index():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_map_axis():
#     raise NotImplementedError()
#
#
# def test_translation_3d():
#     assert np.allclose(
#         act('{"type": "translation", "translation": [1, 2, 3]}', ndim=3),
#         [[2, 4, 6], [5, 7, 9], [8, 10, 12], [11, 13, 15]],
#     )
#
#
# def test_scale_3d():
#     assert np.allclose(
#         act('{"type": "scale", "scale": [1, 2, 3]}', ndim=3),
#         [[1, 4, 9], [4, 10, 18], [7, 16, 27], [10, 22, 36]],
#     )
#
#
# def test_affine_2d():
#     assert np.allclose(
#         act('{"type": "affine", "affine": [1, 2, 3, 4, 5, 6]}', ndim=2),
#         [[8, 20], [14, 38], [20, 56]],
#     )
#
#
# def test_rotation_2d():
#     assert np.allclose(
#         act('{"type": "rotation", "rotation": [0, -1, 1, 0]}', ndim=2),
#         [[-2, 1], [-4, 3], [-6, 5]],
#     )
#
#
# # output from np.matmul(np.array([[5, 6, 7], [8, 9, 10], [0, 0, 1]]), np.vstack([np.transpose((xyz + np.array([1, 2])) * np.array([3, 4])), [1, 1, 1]]))[:-1, :].T
# def test_sequence_2d():
#     assert np.allclose(
#         act(
#             '{"type": "sequence", "transformations": [{"type": "translation", '
#             '"translation": [1, 2]}, {"type": "scale", "scale": [3, 4]}, {"type": "affine", '
#             '"affine": [5, 6, 7, 8, 9, 10]}]}',
#             ndim=2,
#         ),
#         [[133, 202], [211, 322], [289, 442]],
#     )
#
#
# def test_sequence_3d():
#     assert np.allclose(
#         act(
#             '{"type": "sequence", "transformations": [{"type": "translation", '
#             '"translation": [1, 2, 3]}, {"type": "scale", "scale": [4, 5, 6]}, {"type": "translation", '
#             '"translation": [7, 8, 9]}]}',
#             ndim=3,
#         ),
#         [[15, 28, 45], [27, 43, 63], [39, 58, 81], [51, 73, 99]],
#     )
#
#
# @pytest.mark.skip()
# def test_displacements():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_coordinates():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_vector_field():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_inverse_of_inverse_of():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_inverse_of_translation():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_inverse_of_scale():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_inverse_of_affine_2d():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_inverse_of_rotation_2d():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_inverse_of_sequence_2d():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_bijection():
#     raise NotImplementedError()
#
#
# @pytest.mark.skip()
# def test_by_dimension():
#     raise NotImplementedError()
#
#
# def test_to_composition_to_affine():
#     composed0 = get_transformation_from_json(
#         '{"type": "sequence", "transformations": [{"type": "translation", '
#         '"translation": [1, 2]}, {"type": "scale", "scale": [3, 4]}, {"type": "affine", '
#         '"affine": [5, 6, 7, 8, 9, 10]}]}',
#     )
#     composed1 = Sequence(
#         [
#             Sequence(
#                 [
#                     get_transformation_from_json('{"type": "translation", "translation": [1, 2]}'),
#                     get_transformation_from_json('{"type": "scale", "scale": [3, 4]}'),
#                 ],
#             ),
#             Affine(np.array([5, 6, 7, 8, 9, 10])),
#         ]
#     ).to_affine()
#     points = np.array([[1, 2], [3, 4], [5, 6]], dtype=float)
#     expected = np.array([[133, 202], [211, 322], [289, 442]], dtype=float)
#     assert np.allclose(composed0.transform_points(points), expected)
#     assert np.allclose(composed1.transform_points(points), expected)
#
#
# def act(s: str, ndim: int) -> np.array:
#     if ndim == 2:
#         points = np.array([[1, 2], [3, 4], [5, 6]], dtype=float)
#     elif ndim == 3:
#         points = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=float)
#     else:
#         raise ValueError(f"Invalid ndim: {ndim}")
#     return get_transformation_from_json(s).transform_points(points)
#
#
# # TODO: test that the scale, translation and rotation as above gives the same as the rotation as an affine matrices
# # TODO: test also affine transformations to embed 2D points in a 3D space
