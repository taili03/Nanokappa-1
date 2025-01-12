# Copyright (C) 2023-2024, Bruno Hartmann da Silva
# License: MIT

import numpy as np
from pydantic import computed_field
from functools import cached_property
from nanokappa.base import BaseModel, TriVectors, Vector3D


class Triangle(BaseModel, frozen=True):
    vertices: TriVectors[np.float64]

    @computed_field
    @cached_property
    def origin(self) -> Vector3D:
        return self.vertices[0]

    @computed_field
    @cached_property
    def normal(self) -> Vector3D:
        v1 = self.vertices[1] - self.origin
        v2 = self.vertices[2] - self.origin
        cross = np.cross(v1, v2)
        return cross / np.linalg.norm(cross)

    @computed_field
    @cached_property
    def basis(self) -> TriVectors:
        b1 = self.vertices[1] - self.origin
        b2 = self.vertices[2] - self.origin
        return np.vstack((b1, b2, self.normal))

    @computed_field
    @cached_property
    def plane_constant(self) -> float:
        return -np.sum(self.normal * self.origin)

    @computed_field
    @cached_property
    def bounds(self) -> float:
        return np.vstack((self.vertices.min(axis=0), self.vertices.max(axis=0)))

    @computed_field
    @cached_property
    def area(self) -> float:
        v1 = self.vertices[1] - self.origin
        v2 = self.vertices[2] - self.origin
        cross = np.cross(v1, v2)
        return np.linalg.norm(cross) / 2

    @computed_field
    @cached_property
    def centroid(self) -> Vector3D:
        return np.mean(self.vertices, axis=0)

    # SHORTNAMES
    @computed_field
    @cached_property
    def v1(self) -> Vector3D:
        return self.vertices[0, :]

    @computed_field
    @cached_property
    def v2(self) -> Vector3D:
        return self.vertices[1, :]

    @computed_field
    @cached_property
    def v3(self) -> Vector3D:
        return self.vertices[2, :]

    @computed_field
    @cached_property
    def o(self) -> Vector3D:
        return self.v1

    @computed_field
    @cached_property
    def n(self) -> Vector3D:
        return self.normal

    @computed_field
    @cached_property
    def b(self) -> TriVectors:
        return self.basis

    @computed_field
    @cached_property
    def b1(self) -> TriVectors:
        return self.basis[0, :]

    @computed_field
    @cached_property
    def b2(self) -> TriVectors:
        return self.basis[1, :]

    @computed_field
    @cached_property
    def b3(self) -> TriVectors:
        return self.basis[2, :]

    @computed_field
    @cached_property
    def k(self) -> float:
        return self.plane_constant

    @computed_field
    @cached_property
    def A(self) -> float:
        return self.area

    @computed_field
    @cached_property
    def c(self) -> Vector3D:
        return self.centroid
