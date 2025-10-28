# objloader.py
"""
Loader de archivos OBJ para render en PyOpenGL.
"""

from OpenGL.GL import *

class OBJ:
    def __init__(self, filename):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.gl_list = None
        self.load(filename)

    def load(self, filename):
        for line in open(filename, "r", encoding="utf-8", errors="ignore"):
            if line.startswith('#'):
                continue
            values = line.strip().split()
            if not values:
                continue
            if values[0] == 'v':
                self.vertices.append(list(map(float, values[1:4])))
            elif values[0] == 'vn':
                self.normals.append(list(map(float, values[1:4])))
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] == 'f':
                face = []
                for v in values[1:]:
                    w = v.split('/')
                    vi = int(w[0]) - 1
                    ti = int(w[1]) - 1 if len(w) > 1 and w[1] else -1
                    ni = int(w[2]) - 1 if len(w) > 2 and w[2] else -1
                    face.append((vi, ti, ni))
                self.faces.append(face)

    def create_gl_list(self):
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for (vi, ti, ni) in face:
                if ni >= 0 and ni < len(self.normals):
                    glNormal3fv(self.normals[ni])
                if ti >= 0 and ti < len(self.texcoords):
                    glTexCoord2fv(self.texcoords[ti])
                glVertex3fv(self.vertices[vi])
        glEnd()
        glEndList()

    def render(self):
        if self.gl_list is None:
            self.create_gl_list()
        glCallList(self.gl_list)