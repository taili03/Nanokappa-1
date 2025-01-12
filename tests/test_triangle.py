# Copyright (C) 2023-2024, Bruno Hartmann da Silva
# License: MIT

import numpy as np
from nanokappa.geometry import Triangle

vertices = [[0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0]]
vertices = np.array(vertices)

v1, v2, v3 = vertices
o = v1
b1 = v2 - v1
b2 = v3 - v1
A = np.linalg.norm(np.cross(b1, b2))/2
b3 = n = np.cross(b1, b2)/(2*A)
b = np.array([b1, b2, b3])
k = -(o*n).sum()
c = vertices.mean(axis=0)
bounds = np.array([vertices.min(axis=0), vertices.max(axis=0)])


class TestTriangle:
    def test_instantiation(self):
        Triangle(vertices=vertices)
        assert True

    def test_vertices(self):
        tri = Triangle(vertices=vertices)
        assert np.all(tri.vertices == vertices)

    def test_origin(self):
        tri = Triangle(vertices=vertices)
        assert np.all(tri.origin == o)

    def test_normal(self):
        tri = Triangle(vertices=vertices)
        assert np.all(tri.normal == n)

    def test_basis(self):
        tri = Triangle(vertices=vertices)
        assert np.all(tri.basis == b)

    def test_area(self):
        tri = Triangle(vertices=vertices)
        assert tri.area == A

    def test_bounds(self):
        tri = Triangle(vertices=vertices)
        assert np.all(tri.bounds == bounds)

    def test_centroid(self):
        tri = Triangle(vertices=vertices)
        assert np.all(tri.centroid == c)

    def test_plane_constant(self):
        tri = Triangle(vertices=vertices)
        assert tri.plane_constant == k

    def test_shortnames(self):
        shorts = {'v1': v1,
                  'v2': v2,
                  'v3': v3,
                  'b1': b1,
                  'b2': b2,
                  'b3': b3,
                  'b': b,
                  'o': o,
                  'n': n,
                  'k': k,
                  'c': c,
                  'A': A}

        tri = Triangle(vertices=vertices)

        for key, value in shorts.items():
            assert np.all(tri.__getattribute__(key) == value)        
