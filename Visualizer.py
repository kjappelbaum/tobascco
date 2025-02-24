#!/usr/bin/env python
try: 
    import matplotlib
    #matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
except:
    pass
from logging import info, debug, warning, error
import networkx as nx
import numpy as np
import itertools
import Net


class GraphPlot(object):
    
    def __init__(self, net, two_dimensional=False):
        self.fig, self.ax = plt.subplots()
        self.net = net
        self.fontsize = 20 
        self.two_dimensional = two_dimensional
        if two_dimensional:
            self.cell = np.identity(2)
            self.params = net.get_2d_params()
            self.__mkcell()
            self.plot_2d_cell()
        else:
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.params = net.get_3d_params()
            self.cell = np.identity(3)
            self.__mkcell()
            self.plot_3d_cell()

    def plot_2d_cell(self, origin=np.zeros(2), colour='b'):
        xyz_a = (self.cell[0] + origin)/ 2.
        xyz_b = (self.cell[1] + origin)/ 2.
        self.fig.text(xyz_a[0], xyz_a[1], 'a', fontsize=self.fontsize)
        self.fig.text(xyz_b[0], xyz_b[1], 'b', fontsize=self.fontsize)
        all_points = [np.sum(a, axis=0)+origin
                      for a in list(self.powerset(self.cell)) if a]
        all_points.append(origin)
        for s, e in itertools.combinations(np.array(all_points), 2):
            if any([self.zero_cross(s-e, i) for i in self.cell]):
                self.ax.plot(*zip(s, e), color=colour)

    def plot_3d_cell(self, origin=np.zeros(3), colour='b'):

        # add axes labels
        xyz_a = (self.cell[0]+origin)/2. 
        xyz_b = (self.cell[1]+origin)/2. 
        xyz_c = (self.cell[2]+origin)/2. 
        self.ax.text(xyz_a[0], xyz_a[1], xyz_a[2]+0.02, 'a', fontsize=self.fontsize, color=colour)
        self.ax.text(xyz_b[0], xyz_b[1], xyz_b[2], 'b', fontsize=self.fontsize, color=colour)
        self.ax.text(xyz_c[0]+0.02, xyz_c[1], xyz_c[2], 'c', fontsize=self.fontsize, color=colour)

        all_points = [np.sum(a, axis=0)+origin
                      for a in list(self.powerset(self.cell)) if a]
        all_points.append(origin)
        for s, e in itertools.combinations(np.array(all_points), 2):
            if any([self.zero_cross(s-e, i) for i in self.cell]):
                #line([tuple(s), tuple(e)], rgbcolor=(0,0,255))
                self.ax.plot3D(*zip(s, e), color=colour)
                
    def add_point(self, p=np.zeros(3), label=None, colour='r'):
        if self.two_dimensional:
            tp = p + np.array([0.005, 0.005])
        else:
            tp = p + np.array([0.05, -0.05, 0.05])
        pp = np.dot(p.copy(), self.cell)
        tp = np.dot(tp, self.cell)
        try:
            self.ax.scatter(*pp, c=colour, lw=0)
        except TypeError:
            pp = pp.tolist()
            self.ax.scatter(pp, c=colour, lw=0)
        if label:
            if label == "1":
                label = "A"
            elif label == "4":
                label = "C"
            elif label == "9":
                label = "B"
            elif label == "14":
                label = "D"
            elif label == "19":
                label = "E"
            self.ax.text(*tp, s=label, fontsize=self.fontsize, color=colour)

    def add_edge(self, vector, origin=np.zeros(3), label=None, colour='g'):
        """Accounts for periodic boundaries by splitting an edge where
        it intersects with the plane of the boundary conditions.

        """
        p = origin + vector
        p1 = np.dot(origin, self.cell)
        p2 = np.dot(p, self.cell)
        self.ax.plot3D(*zip(p2, p1), color=colour)
        if label:
            pp = (p2 + p1)*0.5
            #pp = pp - np.floor(p)
            #line([tuple(p1), tuple(p2)], rgbcolor=(255,255,0), legend_label=label)
            self.ax.text(*pp, s=label, fontsize=self.fontsize)
    
    def __mkcell(self):
        """Update the cell representation to match the parameters."""
        if self.two_dimensional:
            a_mag, b_mag = self.params[:2]
            gamma = self.params[2]
            a_vec = np.array([a_mag, 0.])
            b_vec = np.array([b_mag * np.cos(gamma), b_mag * np.sin(gamma)])
            self.cell = np.array([a_vec, b_vec])
        else:
            a_mag, b_mag, c_mag = self.params[:3]
            alpha, beta, gamma = self.params[3:]
            a_vec = np.array([a_mag, 0.0, 0.0])
            b_vec = np.array([b_mag * np.cos(gamma), b_mag * np.sin(gamma), 0.0])
            c_x = c_mag * np.cos(beta)
            c_y = c_mag * (np.cos(alpha) - np.cos(gamma) * np.cos(beta)) / np.sin(gamma)
            c_vec = np.array([c_x, c_y, (c_mag**2 - c_x**2 - c_y**2)**0.5])
            self.cell = np.array([a_vec, b_vec, c_vec])
            
    def powerset(self, iterable):
        s = list(iterable)
        return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s)+1))

    def zero_cross(self, vector1, vector2):
        vector1 = vector1/np.linalg.norm(vector1)
        vector2 = vector2/np.linalg.norm(vector2)
        return np.allclose(np.zeros(3), np.cross(vector1, vector2), atol=0.01)
    
    def point_of_intersection(self, p_edge, edge, p_plane, plane_vec1, plane_vec2):
        """
        Returns a point of intersection between an edge and a plane
        p_edge is a point on the edge vector
        edge is the vector direction
        p_plane is a point on the plane
        plane_vec1 represents one of the vector directions of the plane
        plane_vec2 represents the second vector of the plane

        """
        n = np.cross(plane_vec1, plane_vec2)
        n = n / np.linalg.norm(n)
        l = edge / np.linalg.norm(edge)
        
        ldotn = np.dot(l, n)
        pdotn = np.dot(p_plane - p_edge, n)
        if ldotn == 0.:
            return np.zeros(3) 
        if pdotn == 0.:
            return p_edge 
        return pdotn/ldotn*l + p_edge 
    
    def view_graph(self):
        self.net.graph.show(edge_labels=True)
        info("Wait for Xwindow, then press [Enter]")
        raw_input("")

    def view_placement(self, init=(0., 0., 0.), edge_labels=True, sbu_only=[]):
        init = np.array(init)
        # set the first node down at the init position
        V = self.net.graph.nodes()[0]
        V='1'
        edges = self.net.out_edges(V) + self.net.in_edges(V)
        unit_cell_vertices = self.net.vertex_positions(edges, [], pos={V:init})
        for key, value in unit_cell_vertices.items():
            if (sbu_only and key in sbu_only) or (not sbu_only):
                if (key=='1'):
                    key = "A"
                elif(key =="19"):
                    key = "E"
                elif(key =="4"):
                    key="C"
                elif(key=="14"):
                    key="D"
                elif(key=="9"):
                    key="B"
                self.add_point(p=np.array(value), label=key, colour='k')
            elif sbu_only and key not in sbu_only:
                self.add_point(p=np.array(value), label=None, colour='#FF6600') #Blaze Orange
            for edge in self.net.out_edges(key):
                ind = self.net.get_index(edge)
                arc = np.array(self.net.lattice_arcs)[ind]
                el = None
                if edge_labels:
                    el = edge[2]
                self.add_edge(arc, origin=np.array(value), label=el)
            for edge in self.net.in_edges(key):
                ind = self.net.get_index(edge)
                arc = -np.array(self.net.lattice_arcs)[ind]
                el = None
                if edge_labels:
                    el = edge[2]
                self.add_edge(arc, origin=np.array(value), label=el)
        mx = max(self.params[:3])
        mn = min(self.params[:3])
        self.ax.set_xlim3d(-1,mx)
        self.ax.set_ylim3d(0,mx)
        self.ax.set_zlim3d(0,mx)
        self.ax.view_init(elev=17, azim=-96)
        plt.axis('off')
        plt.savefig('name.png', dpi=900)
        #for ii in range(0, 360, 10):
        #    plt.savefig('name.%i.png'%ii, dpi=600)

        #    self.ax.view_init(elev=10.0, azim=ii)
