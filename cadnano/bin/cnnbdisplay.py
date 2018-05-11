# -*- coding: utf-8 -*-
'''For displaying cadnano designs in Jupyter notebooks

uses ``pythreejs`` to do this
'''

from typing import List
import math
import os
import sys
pjoin = os.path.join

from pythreejs import (
    CylinderGeometry,
    CylinderBufferGeometry,
    MeshLambertMaterial,
    Mesh,
    PerspectiveCamera,
    Scene,
    Renderer,
    WebGLRenderer,
    OrbitControls,
    AmbientLight,
    DirectionalLight,
    Vector3,
    Matrix4,
    Object3D
)
import numpy as np
from IPython.display import display
from ipywidgets import HTML, Text, Output, VBox
from traitlets import link, dlink

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(LOCAL_DIR)
sys.path.append(ROOT_DIR)
sys.path.insert(0, '.')

PROJECT_DIR = os.path.dirname(ROOT_DIR)
TEST_PATH = pjoin(PROJECT_DIR, 'cadnano', 'tests')

import cadnano.fileio.decode as cndecode
from cadnano.part.nucleicacidpart import NucleicAcidPart
from cadnano.cntypes import DocT

WIDTH = 600
HEIGHT = 400
CAM_Z = 10.

def normalize(v) -> np.ndarray:
    """Normalize a vector

    Args:
        v: of :obj:`float` of length 3

    Returns:
        ndarray of :obj:`float`, norm of ``v``
    """
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm
# end def

def vec(x):
    return Vector3(x[0], x[1], x[2])

def virtualHelixMesh(   pos1,
                        pos2,
                        radius: float = 1.0,
                        color: str = 'red') -> Mesh:
    pos1 = np.array(pos1, dtype=float)
    pos2 = np.array(pos2, dtype=float)
    delta = pos2 - pos1
    dist = np.linalg.norm(delta)
    c_geometry = CylinderBufferGeometry(  radiusTop=radius,
                                            radiusBottom=radius,
                                            height=dist,
                                            radiusSegments=16
                                    )
    # print(c_geometry.height)
    v2 = normalize(delta)

    # NOTE default direction in Three.js is the Y direction for geometry
    v1 = np.array((0, 1, 0))

    # Calculate angle between Vectors
    angle = math.atan2(
                np.dot(np.cross(v1, v2), v1),
                        np.dot(v1, v2)
            )

    normal_vec = normalize(np.cross(v1, v2)).tolist()

    mid_point = (pos2 + pos1) / 2
    xAxis = [mid_point[0], 0, 0]
    yAxis = [0, mid_point[1], 0]
    zAxis = [0, 0, mid_point[2]]

    mesh = Mesh(geometry=c_geometry,
                material=MeshLambertMaterial(color=color))

    rotm = rotationMatrix(v2)
    mesh.setRotationFromMatrix(threeMatrix(rotm))
    mesh.position = mid_point.tolist()
    return mesh, mid_point
# end def

def renderScene(items: List[Mesh],
                width: int = WIDTH,
                height: int = HEIGHT,
                camera_z: float = CAM_Z,
                mid_point: List[float] = [0, 0, 0]
                ) -> Renderer:
    c = PerspectiveCamera(fov=90, aspect=width/height, near=1, far=1000,
                            position=[0, 0, camera_z], up=[0, 1, 0],
                          children=[DirectionalLight(color='white',
                                                    position=[3, 5, 1],
                                                    intensity=0.5)])
    for x in items:
        x.position = [x.position[i] - mid_point[i] for i in range(3)]

    scene = Scene(children=items+[c, AmbientLight(color='#777777')],
                 background='#000000')

    renderer = Renderer(camera=c,
                            scene=scene,
                            width=width, height=height,
                            controls=[OrbitControls(controlling=c)])

    # scene = Scene(children=items+[c, AmbientLight(color='#777777')])

    # renderer = WebGLRenderer(camera=c,
    #                         scene=scene,
    #                         width=width, height=height,
    #                         controls=[OrbitControls(controlling=c)],
    #                         alpha=True)
    # renderer.setClearColor('#000000', 0.5)
    renderer.render( scene, c )
    return renderer, scene, c
# end def

def displayVHs( part: NucleicAcidPart,
                id_nums: List[int] = [],
                radius: float = 1.0,
                color: str = 'coral',
                width: int = WIDTH,
                height: int = HEIGHT,
                camera_z: float = CAM_Z,
                colors=['coral']):
    if len(id_nums) == 0:
        id_nums = part.getIdNums()
    len_colors = len(colors)

    items = []
    mid_point_sum = (0, 0, 0)
    i = 0
    for id_num in id_nums:
        color = colors[i]
        vh = part.getVirtualHelix(id_num)
        pos1 = vh.getAxisPoint(0)
        pos2 = vh.getAxisPoint(vh.getSize()-1)
        vhm, mid_point = virtualHelixMesh(pos1, pos2, radius=radius, color=color)

        items.append(vhm)
        mid_point_sum += mid_point
        i += 1
        i %= len_colors
    mid_point = mid_point_sum / len(id_nums)
    renderer, sc, cam = renderScene(items, width, height, camera_z, mid_point.tolist())
    display(renderer)
    renderer.render(sc, cam)
# end def

def rotationMatrix(v2: np.ndarray):
    v1 = [0, 1, 0]
    v_cp = normalize(np.cross(v1, v2))
    a0, a1, a2 = v_cp
    dot_p = np.dot(v1, v2)
    I = np.eye(3)
    M = np.array([
                    [0,   -a2, a1],
                    [a2,  0,   -a0],
                    [-a1, a0,  0]
                    ],
                dtype=float)
    R = I + M + M.dot(M)*(1/(1+dot_p))
    return R
# end def

def testDisplay():
    designname = "Nature09_monolith.json"
    inputfile = pjoin(TEST_PATH,
                      "data", designname)
    doc = cndecode.decodeFile(inputfile)
    part = doc.activePart()
    displayVHs(part, camera_z = 70)

def loadFile(filename: str) -> DocT:
    inputfile = pjoin(TEST_PATH,
                      "data", filename)
    doc = cndecode.decodeFile(inputfile)
    return doc

def threeMatrix(m: np.ndarray) -> List[float]:
    '''numpy 3x3 array of shape (3, 3)
    '''
    return [m[0, 0], m[1, 0], m[2, 0],
        m[0, 1], m[1, 1], m[2, 1],
        m[0, 2], m[1, 2], m[2, 2]]
# end def


if __name__ == '__main__':
    mesh = virtualHelixMesh((1,0,0), (2,0,0), 3)
    # testDisplay()
    '''
    ['_trait_values', '_trait_notifiers', '_trait_validators', '_cross_validation_lock',
       '_model_id', '_geometry_metadata', '_material_metadata']
    print(list(mesh.__dict__['_trait_values'].keys()))


    {'_trait_values':
        {'_model_module': 'jupyter-threejs',
        '_model_module_version': '~1.0.0',
        '_model_name': 'MeshModel',
        '_view_count': None,
        '_view_module': None,
        '_view_module_version': '',
        '_view_name': None,
        'castShadow': False,
        'drawMode': 'TrianglesDrawMode',
        'frustumCulled': True,
        'matrixAutoUpdate': True,
        'matrixWorldNeedsUpdate': False,
        'name': '',
        'receiveShadow': False,
        'renderOrder': 0, 'type': 'Mesh',
        'visible': True,
        'position': (1.5, 0.0, 0.0),
        'rotation': (0.0, 1.0, 1.57, 'XYZ'),
    '''
