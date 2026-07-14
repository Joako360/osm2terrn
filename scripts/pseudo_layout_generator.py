import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from math import cos,sin,pi


class ProceduralTransportNetwork:

    def __init__(self):

        self.road=nx.DiGraph()
        self.rail=nx.DiGraph()

        self.crossings=[]
        self.plazas=[]

        self.node_counter=0


    #################################################
    # UTILIDADES
    #################################################

    def new_node_name(self,prefix="N"):

        self.node_counter+=1
        return f"{prefix}_{self.node_counter}"


    def add_node(
        self,
        G,
        x,
        y,
        z=0,
        name=None
    ):

        if name is None:
            name=self.new_node_name()

        G.add_node(
            name,
            x=x,
            y=y,
            z=z
        )

        return name


    def get_pos(self,G,node):

        d=G.nodes[node]

        return np.array([
            d["x"],
            d["y"]
        ])


    #################################################
    # CURVAS
    #################################################

    def bezier_curve(
        self,
        P0,
        P1,
        P2,
        P3,
        n=50
    ):

        P0=np.array(P0)
        P1=np.array(P1)
        P2=np.array(P2)
        P3=np.array(P3)

        curve=[]

        for t in np.linspace(0,1,n):

            p=(

                ((1-t)**3)*P0
                +3*((1-t)**2)*t*P1
                +3*(1-t)*(t**2)*P2
                +(t**3)*P3

            )

            curve.append(tuple(p))

        return curve


    #################################################
    # OFFSET
    #################################################

    def offset_polyline(
        self,
        points,
        offset
    ):

        if len(points) < 2:
            return []

        result=[]
        normals=[]

        for i in range(len(points)-1):

            p1=np.array(points[i])
            p2=np.array(points[i+1])

            d=p2-p1
            d=d/np.linalg.norm(d)

            n=np.array([

                -d[1],
                 d[0]

            ])

            normals.append(n)
            result.append(
                tuple(
                    p1+n*offset
                )
            )

        result.append(
            tuple(
                np.array(points[-1]) + normals[-1]*offset
            )
        )

        return result


    #################################################
    # CARRETERAS
    #################################################

    def create_road_from_points(

        self,
        points,
        road_type="street",
        width=8,
        lanes=2
    ):

        nodes=[]

        for p in points:

            n=self.add_node(

                self.road,
                p[0],
                p[1]

            )

            nodes.append(n)


        for i in range(len(nodes)-1):

            self.road.add_edge(

                nodes[i],
                nodes[i+1],

                road_type=road_type,
                width=width,
                lanes=lanes,
                layer=0

            )

        return nodes


    def create_curved_road(

        self,
        P0,
        P1,
        P2,
        P3,

        road_type="street",
        width=8,
        lanes=2,
        n=50

    ):

        curve=self.bezier_curve(

            P0,
            P1,
            P2,
            P3,
            n

        )

        return self.create_road_from_points(

            curve,
            road_type,
            width,
            lanes
        )


    #################################################
    # DOBLE CALZADA
    #################################################

    def create_dual_carriageway(

        self,
        centerline,
        offset=10,
        width=8,
        lanes=2

    ):

        A=self.offset_polyline(
            centerline,
            offset
        )

        B=self.offset_polyline(
            centerline,
            -offset
        )


        nodesA=self.create_road_from_points(

            A,
            "highway",
            width,
            lanes

        )

        nodesB=self.create_road_from_points(

            B,
            "highway",
            width,
            lanes

        )


        for i in range(len(nodesB)-1):

            if self.road.has_edge(

                nodesB[i],
                nodesB[i+1]

            ):

                data=self.road[
                    nodesB[i]
                ][
                    nodesB[i+1]
                ]

                self.road.remove_edge(
                    nodesB[i],
                    nodesB[i+1]
                )

                self.road.add_edge(

                    nodesB[i+1],
                    nodesB[i],
                    **data

                )


    #################################################
    # ROTONDAS
    #################################################

    def create_roundabout(

        self,
        center=(0,0),
        radius_x=30,
        radius_y=None,
        n=30

    ):

        if radius_y is None:
            radius_y=radius_x


        cx,cy=center

        nodes=[]

        for i in range(n):

            t=2*pi*i/n

            x=cx+radius_x*cos(t)
            y=cy+radius_y*sin(t)

            node=self.add_node(

                self.road,
                x,
                y

            )

            nodes.append(node)


        for i in range(n):

            self.road.add_edge(

                nodes[i],
                nodes[(i+1)%n],

                road_type="roundabout",
                oneway=True

            )

        return nodes


    #################################################
    # TRIANGULOS CANALIZADORES
    #################################################

    def add_channelizing_triangle(

        self,
        center,
        angle,
        size=10

    ):

        x,y=center

        a=np.radians(angle)

        return [

            (x,y),

            (
                x+size*cos(a+0.3),
                y+size*sin(a+0.3)
            ),

            (
                x+size*cos(a-0.3),
                y+size*sin(a-0.3)
            )

        ]


    #################################################
    # PUENTES/TUNELES
    #################################################

    def add_bridge(
        self,
        n1,
        n2
    ):

        self.road[n1][n2]["layer"]=1
        self.road[n1][n2]["structure"]="bridge"


    def add_tunnel(
        self,
        n1,
        n2
    ):

        self.road[n1][n2]["layer"]=-1
        self.road[n1][n2]["structure"]="tunnel"


    #################################################
    # FERROCARRIL
    #################################################

    def create_railway(
        self,
        points
    ):

        nodes=[]

        for p in points:

            n=self.add_node(

                self.rail,
                p[0],
                p[1],
                name=self.new_node_name(
                    "T"
                )
            )

            nodes.append(n)


        for i in range(len(nodes)-1):

            self.rail.add_edge(
                nodes[i],
                nodes[i+1]
            )

        return nodes


    def add_level_crossing(

        self,
        road_edge,
        rail_edge

    ):

        self.crossings.append({

            "road":road_edge,
            "rail":rail_edge

        })


    #################################################
    # PLAZAS
    #################################################

    def create_periodic_plazas(

        self,
        rows,
        cols,
        interval=6,
        size=2

    ):

        for i in range(

            interval//2,
            rows,
            interval

        ):

            for j in range(

                interval//2,
                cols,
                interval

            ):

                self.plazas.append({

                    "row":i,
                    "col":j,
                    "size":size

                })


    def add_central_square(

        self,
        rows,
        cols,
        size=4

    ):

        self.plazas.append({

            "row":rows//2,
            "col":cols//2,
            "size":size

        })


    def is_plaza_cell(
        self,
        r,
        c
    ):

        for p in self.plazas:

            if (

                abs(r-p["row"])<p["size"]
                and
                abs(c-p["col"])<p["size"]

            ):

                return True

        return False


    #################################################
    # GRILLA INTELIGENTE
    #################################################

    def create_smart_grid(

        self,
        rows=30,
        cols=30,
        spacing=100

    ):

        for i in range(rows):

            for j in range(cols):

                if self.is_plaza_cell(
                    i,
                    j
                ):
                    continue

                self.add_node(

                    self.road,

                    j*spacing,
                    i*spacing,

                    name=f"G_{i}_{j}"

                )


        for i in range(rows):

            for j in range(cols):

                cur=f"G_{i}_{j}"

                if cur not in self.road:
                    continue


                right=f"G_{i}_{j+1}"
                down=f"G_{i+1}_{j}"


                if right in self.road:

                    self.road.add_edge(

                        cur,
                        right,

                        road_type="street"

                    )

                if down in self.road:

                    self.road.add_edge(

                        cur,
                        down,

                        road_type="street"

                    )


    #################################################
    # AVENIDAS Y DIAGONALES
    #################################################

    def add_major_avenues(

        self,
        rows,
        cols,
        interval=6

    ):

        for i in range(
            0,
            rows,
            interval
        ):

            for j in range(cols-1):

                a=f"G_{i}_{j}"
                b=f"G_{i}_{j+1}"

                if a in self.road and b in self.road:

                    self.road.add_edge(

                        a,
                        b,

                        road_type="avenue",
                        width=20,
                        lanes=4

                    )


    def add_main_diagonals(
        self,
        rows,
        cols
    ):

        n=min(rows,cols)

        for i in range(n-1):

            a=f"G_{i}_{i}"
            b=f"G_{i+1}_{i+1}"

            if a in self.road and b in self.road:

                self.road.add_edge(

                    a,
                    b,

                    road_type="diagonal",
                    width=25,
                    lanes=4

                )


    #################################################
    # CIRCUNVALACION
    #################################################

    def add_ring_avenue(

        self,
        rows,
        cols,
        spacing=100

    ):

        p=[

            (0,0),
            (cols*spacing,0),
            (cols*spacing,rows*spacing),
            (0,rows*spacing),
            (0,0)

        ]

        self.create_road_from_points(

            p,
            "ring",
            25,
            4

        )


    #################################################
    # VISUALIZADOR
    #################################################

    def plot(self):

        plt.figure(figsize=(12,12))

        for u,v,data in self.road.edges(data=True):

            p1=self.get_pos(
                self.road,
                u
            )

            p2=self.get_pos(
                self.road,
                v
            )

            plt.plot(

                [p1[0],p2[0]],
                [p1[1],p2[1]]

            )


        for u,v in self.rail.edges():

            p1=self.get_pos(
                self.rail,
                u
            )

            p2=self.get_pos(
                self.rail,
                v
            )

            plt.plot(

                [p1[0],p2[0]],
                [p1[1],p2[1]],
                "--"

            )

        plt.axis("equal")
        plt.show()


####################################################
# EJEMPLO TIPO LA PLATA
####################################################

city=ProceduralTransportNetwork()

rows=40
cols=40

city.create_periodic_plazas(
    rows,
    cols
)

city.add_central_square(
    rows,
    cols
)

city.create_smart_grid(
    rows,
    cols,
    spacing=120
)

city.add_major_avenues(
    rows,
    cols
)

city.add_main_diagonals(
    rows,
    cols
)

city.add_ring_avenue(
    rows,
    cols,
    spacing=120
)

curve=city.bezier_curve(

    (0,1000),
    (1000,1200),
    (2500,800),
    (4000,1300)

)

city.create_dual_carriageway(
    curve,
    offset=15
)

city.create_roundabout(
    center=(2200,2200),
    radius_x=60,
    radius_y=40
)

rail=city.bezier_curve(

    (-500,1500),
    (1000,1600),
    (2500,1200),
    (5000,1700)

)

city.create_railway(
    rail
)

city.plot()