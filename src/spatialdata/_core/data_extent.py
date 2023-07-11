from __future__ import annotations

from collections import defaultdict
from functools import singledispatch

import numpy as np
import pandas as pd
from dask.dataframe.core import DataFrame as DaskDataFrame
from geopandas import GeoDataFrame
from multiscale_spatial_image import MultiscaleSpatialImage
from shapely import MultiPolygon, Point, Polygon
from spatial_image import SpatialImage

from spatialdata._core.operations.transform import transform
from spatialdata._core.spatialdata import SpatialData
from spatialdata._types import ArrayLike
from spatialdata.models import get_axes_names
from spatialdata.models._utils import SpatialElement
from spatialdata.models.models import PointsModel
from spatialdata.transformations.operations import get_transformation
from spatialdata.transformations.transformations import (
    BaseTransformation,
)

BoundingBoxDescription = tuple[ArrayLike, ArrayLike, tuple[str, ...]]


def _get_extent_of_circles(circles: GeoDataFrame) -> BoundingBoxDescription:
    """
    Compute the extent (bounding box) of a set of circles.

    Parameters
    ----------
    circles

    Returns
    -------
    The bounding box description.
    """
    assert isinstance(circles.geometry.iloc[0], Point)
    assert "radius" in circles.columns, "Circles must have a 'radius' column."
    axes = get_axes_names(circles)

    centroids = []
    for dim_name in axes:
        centroids.append(getattr(circles["geometry"], dim_name).to_numpy())
    centroids_array = np.column_stack(centroids)
    radius = np.expand_dims(circles["radius"].to_numpy(), axis=1)

    min_coordinates = np.min(centroids_array - radius, axis=0)
    max_coordinates = np.max(centroids_array + radius, axis=0)

    return min_coordinates, max_coordinates, axes


def _get_extent_of_polygons_multipolygons(shapes: GeoDataFrame) -> BoundingBoxDescription:
    """
    Compute the extent (bounding box) of a set of polygons and/or multipolygons.

    Parameters
    ----------
    shapes

    Returns
    -------
    The bounding box description.
    """
    assert isinstance(shapes.geometry.iloc[0], (Polygon, MultiPolygon))
    axes = get_axes_names(shapes)
    bounds = shapes["geometry"].bounds
    min_coordinates = np.array((bounds["minx"].min(), bounds["miny"].min()))
    max_coordinates = np.array((bounds["maxx"].max(), bounds["maxy"].max()))
    return min_coordinates, max_coordinates, axes


@singledispatch
def get_extent(object: SpatialData | SpatialElement, coordinate_system: str = "global") -> BoundingBoxDescription:
    """
    Get the extent (bounding box) of a SpatialData object or a SpatialElement.

    Returns
    -------
    min_coordinate
        The minimum coordinate of the bounding box.
    max_coordinate
        The maximum coordinate of the bounding box.
    axes
        The names of the dimensions of the bounding box
    """
    raise ValueError("The object type is not supported.")


@get_extent.register
def _(e: SpatialData, coordinate_system: str = "global") -> BoundingBoxDescription:
    """
    Get the extent (bounding box) of a SpatialData object: the extent of the union of the extents of all its elements.

    Parameters
    ----------
    e
        The SpatialData object.

    Returns
    -------
    The bounding box description.
    """
    new_min_coordinates_dict = defaultdict(list)
    new_max_coordinates_dict = defaultdict(list)
    for element in e._gen_elements_values():
        transformations = get_transformation(element, get_all=True)
        assert isinstance(transformations, dict)
        coordinate_systems = list(transformations.keys())
        if coordinate_system in coordinate_systems:
            min_coordinates, max_coordinates, axes = get_extent(element, coordinate_system=coordinate_system)
            for i, ax in enumerate(axes):
                new_min_coordinates_dict[ax].append(min_coordinates[i])
                new_max_coordinates_dict[ax].append(max_coordinates[i])
    axes = tuple(new_min_coordinates_dict.keys())
    if len(axes) == 0:
        raise ValueError(
            f"The SpatialData object does not contain any element in the coordinate system {coordinate_system!r}, "
            f"please pass a different coordinate system wiht the argument 'coordinate_system'."
        )
    new_min_coordinates = np.array([min(new_min_coordinates_dict[ax]) for ax in axes])
    new_max_coordinates = np.array([max(new_max_coordinates_dict[ax]) for ax in axes])
    return new_min_coordinates, new_max_coordinates, axes


@get_extent.register
def _(e: GeoDataFrame, coordinate_system: str = "global") -> BoundingBoxDescription:
    """
    Compute the extent (bounding box) of a set of shapes.

    Parameters
    ----------
    shapes

    Returns
    -------
    The bounding box description.
    """
    _check_element_has_coordinate_system(element=e, coordinate_system=coordinate_system)
    if isinstance(e.geometry.iloc[0], Point):
        assert "radius" in e.columns, "Shapes must have a 'radius' column."
        min_coordinates, max_coordinates, axes = _get_extent_of_circles(e)
    else:
        assert isinstance(e.geometry.iloc[0], (Polygon, MultiPolygon)), "Shapes must be polygons or multipolygons."
        min_coordinates, max_coordinates, axes = _get_extent_of_polygons_multipolygons(e)

    return _compute_extent_in_coordinate_system(
        element=e,
        coordinate_system=coordinate_system,
        min_coordinates=min_coordinates,
        max_coordinates=max_coordinates,
        axes=axes,
    )


@get_extent.register
def _(e: DaskDataFrame, coordinate_system: str = "global") -> BoundingBoxDescription:
    _check_element_has_coordinate_system(element=e, coordinate_system=coordinate_system)
    axes = get_axes_names(e)
    min_coordinates = np.array([e[ax].min().compute() for ax in axes])
    max_coordinates = np.array([e[ax].max().compute() for ax in axes])
    return _compute_extent_in_coordinate_system(
        element=e,
        coordinate_system=coordinate_system,
        min_coordinates=min_coordinates,
        max_coordinates=max_coordinates,
        axes=axes,
    )


@get_extent.register
def _(e: SpatialImage, coordinate_system: str = "global") -> BoundingBoxDescription:
    _check_element_has_coordinate_system(element=e, coordinate_system=coordinate_system)
    raise NotImplementedError()
    # return _compute_extent_in_coordinate_system(
    #     element=e,
    #     coordinate_system=coordinate_system,
    #     min_coordinates=min_coordinates,
    #     max_coordinates=max_coordinates,
    #     axes=axes,
    # )


@get_extent.register
def _(e: MultiscaleSpatialImage, coordinate_system: str = "global") -> BoundingBoxDescription:
    _check_element_has_coordinate_system(element=e, coordinate_system=coordinate_system)
    raise NotImplementedError()
    # return _compute_extent_in_coordinate_system(
    #     element=e,
    #     coordinate_system=coordinate_system,
    #     min_coordinates=min_coordinates,
    #     max_coordinates=max_coordinates,
    #     axes=axes,
    # )


def _check_element_has_coordinate_system(element: SpatialElement, coordinate_system: str) -> None:
    transformations = get_transformation(element, get_all=True)
    assert isinstance(transformations, dict)
    coordinate_systems = list(transformations.keys())
    if coordinate_system not in coordinate_systems:
        raise ValueError(
            f"The element does not contain any coordinate system named {coordinate_system!r}, "
            f"please pass a different coordinate system wiht the argument 'coordinate_system'."
        )


def _compute_extent_in_coordinate_system(
    element: SpatialElement,
    coordinate_system: str,
    min_coordinates: ArrayLike,
    max_coordinates: ArrayLike,
    axes: tuple[str, ...],
) -> BoundingBoxDescription:
    """
    Transform the extent from the intrinsic coordinates of the element to the given coordinate system.

    Parameters
    ----------
    element
        The SpatialElement.
    coordinate_system
        The coordinate system to transform the extent to.
    min_coordinates
        Min coordinates of the extent in the intrinsic coordinates of the element.
    max_coordinates
        Max coordinates of the extent in the intrinsic coordinates of the element.
    axes
        The min and max coordinates refer to.

    Returns
    -------
    The bounding box description in the specified coordinate system.
    """
    transformation = get_transformation(element, to_coordinate_system=coordinate_system)
    assert isinstance(transformation, BaseTransformation)
    from spatialdata._core.query._utils import get_bounding_box_corners

    corners = get_bounding_box_corners(axes=axes, min_coordinate=min_coordinates, max_coordinate=max_coordinates)
    df = pd.DataFrame(corners.data, columns=corners.axis.data.tolist())
    points = PointsModel.parse(df, coordinates={k: k for k in axes})
    transformed_corners = transform(points, transformation).compute()
    min_coordinates = transformed_corners.min().to_numpy()
    max_coordinates = transformed_corners.max().to_numpy()
    return min_coordinates, max_coordinates, axes
