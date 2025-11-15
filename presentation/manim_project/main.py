import os
import random

import numpy as np
from scipy.integrate import solve_ivp
import math

from manim import *
from manim_slides import Slide

import functools

DEFAULT_COLOR = ManimColor.from_rgb([0.01,0.01,0.01])  # Almost black

THETA_COLOR = RED
THETA_DOT_COLOR = GREEN
THETA_DDOT_COLOR = BLUE

# Skip all the parametric waiting time ( slow down incremental development)
DEBUG = False

def dep_default_color(func):
    """Sets default color to Default color"""

    def wrapper(*args, color=DEFAULT_COLOR, **kwargs):
        return func(*args, color=color, **kwargs)

    return wrapper

def default_color(cls):
    """Sets default color to Default color for class initializers"""

    init_func = cls.__init__

    @functools.wraps(init_func)
    def new_init(self, *args, color=DEFAULT_COLOR, **kwargs):
        init_func(self, *args, color=color, **kwargs)

    return new_init

def color_mathtext(cls:MathTex):
    """Sets default color to Default color for MathTex and Tex"""

    init_func = cls.__init__

    @functools.wraps(init_func)
    def new_init(self, *args, substrings_to_isolate=[], **kwargs):
        # Need to report bug to Manim about the substrings_to_isolate creating issue with Tex class (DVI convert)
        # Highly unstable +[r"\ddot{\theta}",r"\dot{\theta}",r"\theta"]
        init_func(self, *args, substrings_to_isolate=substrings_to_isolate+[r"\ddot{\theta}",r"\dot{\theta}",r"\theta"], **kwargs)

        self.set_color_by_tex(r"\theta",THETA_COLOR)
        self.set_color_by_tex(r"\dot{\theta}",THETA_DOT_COLOR)
        self.set_color_by_tex(r"\ddot{\theta}",THETA_DDOT_COLOR)

    return new_init

def Paragraph(*strs, alignment=LEFT, direction=DOWN, **kwargs):
    texts = VGroup(*[Text(s, **kwargs) for s in strs]).arrange(direction)

    if len(strs) > 1:
        for text in texts[1:]:
            text.align_to(texts[0], direction=alignment)

    return texts

# --- Pendulum Definition within a Class ---

class Pendulum:
    """
    A class to encapsulate the state and physics of a simple pendulum.
    
    This class uses scipy.integrate.solve_ivp for accurate numerical integration.
    """
    def __init__(self, theta0=math.pi / 4, theta_dot0=0.0, L=1.0, g=9.81):
        """
        Initializes the pendulum.
        
        Args:
            theta0 (float): Initial angle in radians.
            theta_dot0 (float): Initial angular velocity in rad/s.
            L (float): Length of the pendulum in meters.
            g (float): Acceleration due to gravity in m/s^2.
        """
        self.L = L
        self.g = g

        self.active=False
        
        # State vector: [theta, theta_dot]
        self.state = np.array([theta0, theta_dot0])
        self.time = 0.0
        
        # Time series data: [time, theta, theta_dot, theta_ddot]
        theta_ddot0 = -(self.g / self.L) * math.sin(theta0)
        self.history = np.array([[self.time, theta0, theta_dot0, theta_ddot0]])

    def is_active(self):
        """Returns whether the pendulum simulation is active."""
        return self.active

    def activate(self):
        """Activate the pendulum simulation."""
        self.active=True

    def deactivate(self):
        """Deactivate the pendulum simulation."""
        self.active=False

    def reset_time(self):
        """Resets the pendulum's time to zero and clears history."""
        self.time = 0.0
        theta = self.state[0]
        theta_dot = self.state[1]
        theta_ddot = -(self.g / self.L) * math.sin(theta)
        self.history = np.array([[self.time, theta, theta_dot, theta_ddot]])

    def get_theta(self):
        """Returns the current angle of the pendulum in radians."""
        return self.state[0]
    
    def get_local_vector(self):
        """Returns the unit vector pointing along the pendulum's rod."""
        theta = self.get_theta()
        return self.L*(RIGHT*math.sin(theta)-UP*math.cos(theta))
    
    def get_theta_dot(self):
        """Returns the current angular velocity of the pendulum in radians per second."""
        return self.state[1]
    
    def get_time(self):
        """Returns the current time in seconds."""
        return self.time
    
    def get_period(self):
        """Returns the approximate period of the pendulum in seconds."""
        return 2 * math.pi * math.sqrt(self.L / self.g)
    
    def get_times(self):
        """Returns the array of recorded time values."""
        return self.history[:, 0]
    
    def get_thetas(self):
        """Returns the array of recorded theta values."""
        return self.history[:, 1]
    
    def get_thetas_dot(self):
        """Returns the array of recorded theta_dot values."""
        return self.history[:, 2]
    
    def get_thetas_ddot(self):
        """Returns the array of recorded theta_ddot values."""
        return self.history[:, 3]

    def _ode_system(self, t, S):
        """
        Defines the system of ordinary differential equations.
        
        This is the function that solve_ivp will integrate.
        
        Args:
            t (float): Current time (required by solve_ivp, but not used in this simple system).
            S (np.ndarray): State vector [theta, theta_dot].
            
        Returns:
            list: The rate of change of the state vector [d(theta)/dt, d(theta_dot)/dt].
        """
        theta, theta_dot = S
        dtheta_dt = theta_dot
        dtheta_dot_dt = -(self.g / self.L) * math.sin(theta)
        return [dtheta_dt, dtheta_dot_dt]

    def advance(self, dt):
        """
        Advances the pendulum's state by a time step dt using a high-quality solver.
        
        Args:
            dt (float): The time step in seconds.
        """
        # Define the time span for the integration
        time_span = [self.time, self.time + dt]
        
        # Use solve_ivp to find the solution at the end of the time step
        # 'RK45' is the default and a good general-purpose choice.
        # 't_eval' tells the solver we only care about the final state.
        solution = solve_ivp(
            fun=self._ode_system, 
            t_span=time_span, 
            y0=self.state, 
            method='RK45',
            # t_eval=[self.time + dt]
        )
        
        # Update the state to the new state computed by the solver

        # print(solution.y)
        self.state = solution.y[:, -1]
        
        # Update the time
        self.time += dt
        
        # Calculate acceleration and append to history
        theta = self.state[0]
        theta_dot = self.state[1]
        theta_ddot = -(self.g / self.L) * math.sin(theta)
        self.history = np.vstack([self.history, [self.time, theta, theta_dot, theta_ddot]])

    def __str__(self):
        """String representation for easy printing."""
        angle_deg = math.degrees(self.state[0])
        velocity_rads = self.state[1]
        return f"Time: {self.time:.2f}s, Angle: {angle_deg:.2f}°, Velocity: {velocity_rads:.2f} rad/s"


SINDY_LINE_LENGHT = 3
SINDY_LINE_WIDTH = 0.25
SINDY_MATRIX_CLEARANCE = 0.1

class SindyMatrix(VMobject):

    # Matrix of the lines contains Vgroup of the title and the line
    lines= None
    
    # Matrix MObjectMatrix
    matrix = None

    def _default_title_wrapper(text,i,j):
        return f"\\boldsymbol{{{text}_{{{i+1},{j+1}}}}}"

    def __init__(self,unit_matrix,base_name="f",title_wrapper=_default_title_wrapper,reverse_color=False,**kwargs):
        super().__init__(**kwargs)


        self._create_sindy_matrix(unit_matrix,base_name=base_name,title_wrapper=title_wrapper,reverse_color=reverse_color)
        

    def get_brackets(self):

        return self.matrix.get_brackets()
    
    def get_contents(self):

        return self.matrix.get_entries()
    
    def get_lines(self):

        lines_vgroup = VGroup()

        for i in range(len(self.lines)):

            line = VGroup()
            for j in range(len(self.lines[0])):
                if isinstance(self.lines[i][j],VGroup):
                    line.add(self.lines[i][j])

            lines_vgroup.add(line)

        return lines_vgroup

    def _create_sindy_line(self,color=DEFAULT_COLOR,divide=1,title=""):

        #line = Line(start=ORIGIN,end=DOWN*SINDY_LINE_LENGHT/divide+RIGHT*0.01,buff=0,stroke_width=SINDY_LINE_WIDTH,color=color)
        line = RoundedRectangle(height=SINDY_LINE_LENGHT/divide,width=SINDY_LINE_WIDTH,fill_color=color,color=color,corner_radius=SINDY_LINE_WIDTH/4).set_fill(color,opacity=1)

        if title != "":
            title_mob = MathTex(title,color=color).scale(0.75).next_to(line,UP,buff=0.1)
        else:
            title_mob = VMobject()

        height = SINDY_LINE_LENGHT/divide  + title_mob.height + 0.1
        width = SINDY_LINE_WIDTH + title_mob.width + 0.1

        return VGroup(title_mob,line),(height,width)
    
    def remove_matrix_content(self):

       self.matrix.get_entries().set_opacity(0)
    
    def _create_sindy_matrix(self,unit_matrix,base_name="f",title_wrapper=_default_title_wrapper,reverse_color=False):

        color_list = ["BLUE","TEAL","GREEN","GOLD","RED","MAROON","PURPLE"]
        letter_list = ["A","B","C","D","E"]

        rows = len(unit_matrix)
        cols = len(unit_matrix[0])

        if rows>=len(letter_list) :
            raise ValueError("Too many rows for letter representation")
        if cols>=len(color_list):
            raise ValueError("Too many columns for color representation")
        
        self.lines = np.zeros((rows,cols),dtype=object)

        max_height = 0
        max_width = 0

        for i in range(len(unit_matrix)):
            for j in range(len(unit_matrix[0])):

                if unit_matrix[i][j] == 1:

                    line,(height,width) = self._create_sindy_line(color=eval(color_list[ -j-1 if reverse_color else j]+"_"+letter_list[i]),divide= rows,title=title_wrapper(base_name,i,j))
                    max_height = max(max_height,height)
                    max_width = max(max_width,width)
                    self.lines[i][j] = line
                else:

                    self.lines[i][j] = VMobject()


        self.matrix = MobjectMatrix(
            self.lines,
            v_buff=max_height+SINDY_MATRIX_CLEARANCE*1,
            h_buff=max_width+SINDY_MATRIX_CLEARANCE*2,
        )

        self.add(self.matrix)


Tex.__init__ = default_color(Tex)
Text.__init__ = default_color(Text)

MathTex.__init__ = default_color(MathTex)
MathTex.__init__ = color_mathtext(MathTex)

Line.__init__ = default_color(Line)
Dot.__init__ = default_color(Dot)
Brace.__init__ = default_color(Brace)
Arrow.__init__ = default_color(Arrow)
Angle.__init__ = default_color(Angle)
Integer.__init__ = default_color(Integer)
Paragraph.__init__ = default_color(Paragraph)
DecimalNumber.__init__ = default_color(DecimalNumber)

global_slide_counter = 0

section_name = [
    "Introduction",
    "SINDY",
    "Entropy and input information",
    "Implicit and explicit system",
    "Results",
    "Future works",
    "QA time",
]




class Item:
    def __init__(self, initial=1):
        self.value = initial

    def __repr__(self):
        s = repr(self.value)
        self.value += 1
        return s
    
class BaseSlide(Slide):

    max_duration_before_split_reverse = None
    wait_time_between_slides = 0.1

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)

        random.seed(1234)

        # Colors
        self.BS_COLOR = BLUE_D
        self.UE_COLOR = MAROON_D
        self.SIGNAL_COLOR = BLUE_B
        self.WALL_COLOR = LIGHT_BROWN
        self.INVALID_COLOR = RED
        self.VALID_COLOR = "#28C137"
        self.IMAGE_COLOR = "#636463"
        self.X_COLOR = DARK_BROWN

        self.camera.background_color = WHITE 

        # Coordinates
        self.UL = Dot().to_corner(UL).get_center()
        self.UR = Dot().to_corner(UR).get_center()
        self.DL = Dot().to_corner(DL).get_center()
        self.DR = Dot().to_corner(DR).get_center()

        # Font sizes
        self.TITLE_FONT_SIZE = 48
        self.CONTENT_FONT_SIZE = 0.5 * self.TITLE_FONT_SIZE
        self.MEDIUM_CONTENT_FONT_SIZE = 0.3 * self.TITLE_FONT_SIZE
        self.SOURCE_FONT_SIZE = 0.2 * self.TITLE_FONT_SIZE

        # Mutable variables
        self.slide_number = Integer(global_slide_counter).to_corner(DR)
        self.slide_title = Text(
            "", color=DEFAULT_COLOR, font_size=self.TITLE_FONT_SIZE
        ).to_corner(UL)
        self.add_to_canvas(slide_number=self.slide_number)

        self.tex_template = TexTemplate()
        self.tex_template.add_to_preamble(
            r"""
        \usepackage{siunitx}
        \usepackage{amsmath}
        \newcommand{\ts}{\textstyle}
        """
        )

    def next_slide_number_animation(self):
        global global_slide_counter
        global_slide_counter = global_slide_counter + 1

        return self.slide_number.animate(run_time=0.5).set_value(
            global_slide_counter
        )
    
    def next_slide_title_animation(self, title, **kwargs):
        if self.slide_title.text == "":
            self.slide_title = Text(
                title, color=DEFAULT_COLOR, font_size=self.TITLE_FONT_SIZE, **kwargs
            ).to_corner(UL)
            self.add_to_canvas(slide_title=self.slide_title)
            return FadeIn(
                self.slide_title
            )

        else:
            return Transform(
                self.slide_title,
                Text(title, font_size=self.TITLE_FONT_SIZE)
                .move_to(self.slide_title)
                .align_to(self.slide_title, LEFT),
            )
    
    def new_clean_slide(self, title, contents=None,**kwargs):
        
        if len(self.mobjects_without_canvas)>0 or contents is not None:
            self.play(
                self.next_slide_number_animation(),
                self.next_slide_title_animation(title,**kwargs),
                self.wipe(
                    self.mobjects_without_canvas if self.mobjects_without_canvas else [],
                    contents if contents else [],
                    return_animation=True,
                ),
            )
        else:
            self.play(self.next_slide_number_animation(),self.next_slide_title_animation(title))



class Main(BaseSlide):


    def construct_intro(self):

        title = Text(
            "Discovering Nonlinear Dynamics by Simultaneous Lagrangian and Newtonian"
        ).scale(0.5)
        title_2 = Text ("Identification for Implicit and Explicit Sparse Identification").scale(0.5)
        author_date = (
            Text("Eymeric Chauchat C4TM1417 - 18th November 2025")
            .scale(0.3)
        )

        intro_group = VGroup(title,title_2,author_date).arrange(DOWN)

        self.play(
            self.next_slide_number_animation(),
            Create(intro_group)
            )

        self.next_slide(notes=" # Contents of the presentation")

        i = Item()

        contents = Paragraph(
            *[
                f"{i}. {section}"
                for section in section_name
            ],
            font_size=self.CONTENT_FONT_SIZE,
        ).align_to(self.UL, LEFT).shift(RIGHT*1)

        self.new_clean_slide("Contents",contents=contents)

    def construct_introduction(self):

        self.next_slide(notes=" # Introduction to SINDy")

        i = Item()

        contents = Paragraph(
            *[
                f"{i}. {subsection}"
                for subsection in [
                    "What has been done in SINDy",
                    "My SINDy",
                ]
            ],
            font_size=self.CONTENT_FONT_SIZE,
        ).align_to(self.UL, LEFT).shift(RIGHT*1)

        self.new_clean_slide("1.1 Introduction",contents=contents)

    def construct_what_is_sindy(self):

        self.next_slide(notes=" # What is SINDy")
        self.new_clean_slide(r"1.2 What is SINDy")


        pendulum_L = 1

        PendulumObject = Pendulum(theta0=math.pi-0.05,L=pendulum_L,g=15,theta_dot0=.0)


        PendulumOrigin = Dot(radius=0.1,color=BLUE)
        PendulumExtreme = Dot(radius=0.1,color=BLUE).move_to(PendulumOrigin.get_center()).shift(PendulumObject.get_local_vector())

        def get_rod():
            return Line(PendulumOrigin.get_center(),PendulumExtreme.get_center(),color=DEFAULT_COLOR)

        PendulumRod = always_redraw(get_rod)
        PendulumGroup = VGroup(PendulumExtreme,PendulumRod,PendulumOrigin)


        sindy_text = self.slide_title[-5:-1].copy()

        sindy_text_deployed = VGroup(Text("Sparse"),Text("Identification of"),Text("Nonlinear"),Text("Dynamics")).arrange_in_grid(rows=4,cols=1,col_alignments="l").shift(LEFT*3)

        self.next_slide(notes="What does SINDy stand for ?")

        self.play(
            LaggedStart(
                *[ letter.animate.move_to(sindy_text_deployed[i][0].get_center()) for i,letter in enumerate(sindy_text) ],
                lag_ratio=0.25
            )
            )
        
        for i,text in enumerate(sindy_text_deployed):
            self.play(AddTextLetterByLetter(text) )
            self.remove(sindy_text[i])

        self.next_slide(notes="Now we will focus on Identification of Nonlinear Dynamics")

        sindy_text_unified = Text("Sparse Identification of Nonlinear Dynamics").scale(0.5).next_to(self.slide_title,DOWN,aligned_edge=LEFT)

        text_indices = [(0,6),(6,21),(21,30),(30,39)]

        self.play(
            *[
                word.animate.move_to(sindy_text_unified[start:end] ).scale(0.5)
                for word,(start,end) in zip(sindy_text_deployed,text_indices)
            ]
            )
        
        self.play(
            *[word.animate.set_color(RED_E)  for word in sindy_text_deployed[1:]]
        )

        self.next_slide(notes=" Let's introduce our pendulum")

        self.play(Create(PendulumGroup))

        self.next_slide(notes=" Our pendulum is govern by equation following a paradigm")

        newton_equation = MathTex(r" \sum F \left( \theta , \dot{\theta} \right)",r"=", r"m \ddot{\theta} ").shift(RIGHT*2)

        self.play(
            PendulumGroup.animate.shift(LEFT*1.5),
            Write(newton_equation)
            )

        self.next_slide(notes=" There is our pendulum equation")

        ode_equation = MathTex(r"\ddot{\theta} + \frac{g}{L} \sin(\theta)",r"=",r"0").move_to(newton_equation)

        self.play(
            TransformMatchingTex(newton_equation,ode_equation),
            )

        self.next_slide(notes=" Let's give a pinch of energy to the pendulum",loop=True)

        def update_rod(rod:Mobject):
            rod.put_start_and_end_on(PendulumOrigin.get_center(),PendulumExtreme.get_center())

        def update_pendulum(origin_mob:Mobject, dt):
            PendulumObject.advance(dt)
            origin_mob.move_to(PendulumOrigin.get_center()).shift(PendulumObject.get_local_vector())

        PendulumObject.activate()
        PendulumExtreme.add_updater(update_pendulum)
        PendulumRod.add_updater(update_rod)

        if DEBUG:
            self.wait(3)
        else:
            self.wait(4*PendulumObject.get_period(),stop_condition=lambda: (PendulumObject.get_theta() > math.pi-0.1) and (PendulumObject.get_time()>3) )

        PendulumObject.deactivate()
        PendulumExtreme.remove_updater(update_pendulum)
        PendulumRod.remove_updater(update_rod)

        self.next_slide(notes=" Let's analyze the data of our pendulum")

        PendulumGroup.generate_target()
        PendulumGroup.target.next_to(sindy_text_deployed,DOWN,aligned_edge=LEFT).shift(RIGHT*0.5+DOWN*0.5)

        self.play(
            ode_equation.animate.move_to(PendulumGroup.target.get_center()).align_to(self.UR,RIGHT).shift(LEFT*0.5),
            MoveToTarget(PendulumGroup),
            )

        simulation_time=10

        x_scale = 0.5
        y_scale = 0.5

        theta_axes = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-math.pi, math.pi, 2],
            x_length=simulation_time*x_scale,
            y_length=y_scale*2,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }
        )
        theta_axes.shift(PendulumOrigin.get_center()- theta_axes.get_origin() +RIGHT*(pendulum_L+0.5))

        theta_axes_label= theta_axes.get_axis_labels(
            x_label=Tex("Time (s)",color=DEFAULT_COLOR).scale(0.5),
            y_label=MathTex(r"\theta",color=DEFAULT_COLOR).scale(0.5),
        )

        # The curve that will be traced when pendulum moves
        theta_curve = VGroup()
        PendulumObject.reset_time()
        curve_start = theta_axes.get_origin()+np.array([x_scale*PendulumObject.get_time(), PendulumObject.get_theta()/math.pi*y_scale, 0])

        theta_curve.add(Line(curve_start,curve_start))

        def get_curve():
            if PendulumObject.is_active() == False:
                return theta_curve
            
            last_line_end = theta_curve[-1].get_end()
            new_point = np.array([x_scale*PendulumObject.get_time(), PendulumObject.get_theta()/math.pi*y_scale, 0])
            new_line = Line(last_line_end,theta_axes.get_origin()+new_point,color=THETA_COLOR)
            theta_curve.add(new_line)
            return theta_curve
        
        self.play(Create(theta_axes),Create(theta_axes_label))

        PendulumObject.activate()
        PendulumExtreme.add_updater(update_pendulum)
        PendulumRod.add_updater(update_rod)
        
        theta_curve = always_redraw(get_curve)

        self.add(theta_curve)
        if DEBUG:
            self.wait(simulation_time)
        else:
            self.wait(simulation_time,stop_condition=lambda: PendulumObject.get_time()>=simulation_time )

        PendulumObject.deactivate()
        PendulumExtreme.remove_updater(update_pendulum)
        PendulumRod.remove_updater(update_rod)

        ThetaAxesGroup = VGroup(theta_axes,theta_axes_label,theta_curve)

        self.next_slide(notes="We also need velocity and acceleration.")

        ThetaAxesGroup.generate_target()
        ThetaAxesGroup.target.shift(UP*0.5)

        theta_dot_axes = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-8, 8, 2],
            x_length=simulation_time*x_scale,
            y_length=y_scale*2,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }
        ).next_to(ThetaAxesGroup.target,DOWN,0.5,LEFT)

        theta_dot_text = MathTex(r"\dot{\theta}",color=DEFAULT_COLOR).scale(0.5)

        theta_dot_axes_label= theta_dot_axes.get_axis_labels(
            y_label=theta_dot_text,
        )

        theta_dot_curve = theta_dot_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_dot(),line_color=THETA_DOT_COLOR,add_vertex_dots=False)

        theta_ddot_axes = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-16, 16, 2],
            x_length=simulation_time*x_scale,
            y_length=y_scale*2,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }
        ).next_to(theta_dot_axes,DOWN,0.5,LEFT)

        ddot_theta=MathTex(r"\ddot{\theta}",color=DEFAULT_COLOR).scale(0.5)

        theta_ddot_axes_label= theta_ddot_axes.get_axis_labels(
            y_label=ddot_theta,
        )

        theta_ddot_curve = theta_ddot_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_ddot(),line_color=THETA_DDOT_COLOR,add_vertex_dots=False)

        theta_ddot_axes_group = VGroup(theta_ddot_axes,theta_ddot_curve,ddot_theta)
        
        self.play(
            MoveToTarget(ThetaAxesGroup),
            Create(theta_dot_axes),Create(theta_dot_curve),Create(theta_dot_text),
            Create(theta_ddot_axes),Create(theta_ddot_curve),Create(ddot_theta),
        )

        theta_curve_simplified = theta_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas(),line_color=THETA_COLOR,add_vertex_dots=False)

        # Simplify structure of the curve
        self.remove(theta_curve)
        self.add(theta_curve_simplified)

        theta_curve = theta_curve_simplified

        self.next_slide(notes=" We have now all the data to perform SINDy")

        Data_Group = VGroup(
                theta_axes,
                theta_axes_label,
                theta_curve,
                theta_dot_axes,
                theta_dot_curve,
                ddot_theta,
                theta_ddot_axes,
                theta_ddot_curve,
                theta_dot_text,
            )

        self.play(
            Uncreate(PendulumGroup),
            Uncreate(ode_equation),
            Data_Group.animate.scale(0.5).to_corner(UR),
            self.next_slide_number_animation()
        )

        self.next_slide(notes="Let's get back to our paradigm newton")

        newton_equation = MathTex(r" \sum F \left( \theta , \dot{\theta} \right)",r"=", r"m \ddot{\theta} ")

        self.play(
            Write(newton_equation)
        )

        self.next_slide(notes="We want to model a system and not only match our data")

        force_term = newton_equation[0:5]
        other_term = newton_equation[5:]

        force_equation_box = SurroundingRectangle(force_term,color=YELLOW,buff=0.2)

        self.play(
            Create(force_equation_box)
        )

        self.next_slide(notes="Let's reformulate what is a system")

        system_box = Rectangle(color=YELLOW_E,height=2,width=3)
        input_arrow = Arrow(start=system_box.get_left()+LEFT*3,end=system_box.get_left(),buff=0.0)
        output_arrow = Arrow(start=system_box.get_right(),end=system_box.get_right()+RIGHT*3,buff=0.0)
        system_label = Text("System",color=YELLOW_E).move_to(system_box.get_center())

        input_label = MathTex(r"\theta , \dot{\theta}").next_to(input_arrow,UP)
        output_label = MathTex(r"\ddot{\theta}").next_to(output_arrow,UP)

        system = VGroup(system_box,input_arrow,output_arrow,system_label,input_label,output_label).shift(DOWN*1.8)

        # Until now 1mn from the start of the construct

        self.play(
            Uncreate(other_term),
            ReplacementTransform(VGroup(force_term,force_equation_box),system)
        )

        self.next_slide(notes="Let's reformulate what is a system")

        data_surrounding = SurroundingRectangle(Data_Group,color=PURPLE,buff=0.3)

        sindy_explanation = Text("SINDy generates system from data",t2c={"system":YELLOW_E,"data":PURPLE}).shift(LEFT*1)

        self.play(
            Create(data_surrounding),
            Write(sindy_explanation)
        )

        self.next_slide(notes="Now we can dive into the sparse argument of SINDy")

        self.play(
            Uncreate(sindy_explanation),
            Uncreate(data_surrounding),
            Uncreate(system),
            sindy_text_deployed[0].animate.set_color(RED_E),
            self.next_slide_number_animation(),
            *[word.animate.set_color(DEFAULT_COLOR)  for word in sindy_text_deployed[1:]]
        )

        catalog_text = Text("Catalog of candidate functions",t2c={"Catalog":YELLOW_E,"candidate functions":YELLOW_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_text_deployed,DOWN,aligned_edge=LEFT)

        sin_theta =MathTex(r"\sin(\theta)")
        cos_theta =MathTex(r"\cos(\theta)")
        theta_dot =MathTex(r"\dot{\theta}")
        theta_dot2 =MathTex(r"\dot{\theta}^2")

        equation_list = VGroup(sin_theta,cos_theta,theta_dot,theta_dot2).arrange(DOWN,buff=0.5).next_to(catalog_text,DOWN).shift(DOWN*0.5)


        self.play(
            Write(catalog_text),
            Write(equation_list)
        )

        self.next_slide(notes="We need to take a few of these term to reconstruct our system")

        axes_sin_theta = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-1.5, 1.5, 1],
            x_length=simulation_time*x_scale,
            y_length=0.75,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }
        )
        axes_sin_labels= axes_sin_theta.get_axis_labels(
            y_label=sin_theta.generate_target().scale(0.5),
        )

        axes_cos_theta = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-1.5, 1.5, 1],
            x_length=simulation_time*x_scale,
            y_length=0.75,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }
        )
        axes_cos_labels= axes_cos_theta.get_axis_labels(
            y_label=cos_theta.generate_target().scale(0.5),
        )

        axes_theta_dot_2 = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-10, 10, 5],
            x_length=simulation_time*x_scale,
            y_length=0.75,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }
        )
        axes_theta_dot_2_labels= axes_theta_dot_2.get_axis_labels(
            y_label=theta_dot.generate_target().scale(0.5),
        )

        axes_theta_dot_sqr = Axes(
            x_range=[0, simulation_time, 1],
            y_range=[-100, 100, 5],
            x_length=simulation_time*x_scale,
            y_length=0.75,
            tips=False,
            x_axis_config={
                "decimal_number_config" :{
                    "color": DEFAULT_COLOR,
                    "num_decimal_places": 0,
                },
                "numbers_to_include": np.arange(0, simulation_time, 2),
                "numbers_with_elongated_ticks": np.arange(0, simulation_time, 2),
            },
            axis_config={
                "color": DEFAULT_COLOR,
            },
            y_axis_config={
                "include_ticks":False
            }

        )
        axes_theta_dot_sqr_labels= axes_theta_dot_sqr.get_axis_labels(
            y_label=theta_dot2.generate_target().scale(0.5),
        )

        axes_group = VGroup(
            VGroup(axes_sin_theta,axes_sin_labels),
            VGroup(axes_cos_theta,axes_cos_labels),
            VGroup(axes_theta_dot_2,axes_theta_dot_2_labels),
            VGroup(axes_theta_dot_sqr,axes_theta_dot_sqr_labels)
            ).arrange_in_grid(rows=4,cols=1,buff=0.1)
        
        times_1 = MathTex(r"\times").next_to(axes_sin_theta,LEFT)
        times_2 = MathTex(r"\times").next_to(axes_cos_theta,LEFT)
        times_3 = MathTex(r"\times").next_to(axes_theta_dot_2,LEFT)
        times_4 = MathTex(r"\times").next_to(axes_theta_dot_sqr,LEFT)
        
        a = MathTex(r"a").next_to(times_1,LEFT)
        b = MathTex(r"b").next_to(times_2,LEFT)
        c = MathTex(r"c").next_to(times_3,LEFT)
        d = MathTex(r"d").next_to(times_4,LEFT)
        plus_1 = MathTex(r"+").next_to(axes_sin_theta,RIGHT)
        plus_2 = MathTex(r"+").next_to(axes_cos_theta,RIGHT)
        plus_3 = MathTex(r"+").next_to(axes_theta_dot_2,RIGHT)

        math_group = VGroup(
            a,
            b,
            c,
            d,
            plus_1,
            plus_2,
            plus_3,
            times_1,
            times_2,
            times_3,
            times_4,
        )
        
        theta_ddot_axes_group.generate_target()

        theta_ddot_axes_group.target.scale(2)

        equal = MathTex(r"=").scale(1)

        VGroup(VGroup(axes_group,math_group),equal,theta_ddot_axes_group.target).arrange(RIGHT,buff=0.5).next_to(catalog_text,DOWN).shift(DOWN*0.1).set_x(0)

        sin_theta_curve = axes_sin_theta.plot_line_graph(PendulumObject.get_times(),np.sin(PendulumObject.get_thetas()),line_color=TEAL,add_vertex_dots=False)

        cos_theta_curve = axes_cos_theta.plot_line_graph(PendulumObject.get_times(),np.cos(PendulumObject.get_thetas()),line_color=GOLD,add_vertex_dots=False)

        theta_dot_2_curve = axes_theta_dot_2.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_dot(),line_color=THETA_DOT_COLOR,add_vertex_dots=False)

        theta_dot_sqr_curve = axes_theta_dot_sqr.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_dot()**2,line_color=MAROON,add_vertex_dots=False)

        self.play(
            MoveToTarget(sin_theta),
            MoveToTarget(cos_theta),
            MoveToTarget(theta_dot),
            MoveToTarget(theta_dot2),
            Create(axes_sin_theta),
            Create( axes_cos_theta),
            Create( axes_theta_dot_2),
            Create( axes_theta_dot_sqr),
            ReplacementTransform(theta_curve.copy(),sin_theta_curve),
            ReplacementTransform(theta_curve,cos_theta_curve),
            ReplacementTransform(theta_dot_curve.copy(),theta_dot_2_curve),
            ReplacementTransform(theta_dot_curve,theta_dot_sqr_curve),
            Uncreate(theta_dot_axes),
            Uncreate(theta_axes),
            Uncreate(theta_dot_axes_label),
            Uncreate(theta_axes_label),
            MoveToTarget(theta_ddot_axes_group),
        )

        self.next_slide(notes="We need to select the right terms")

        self.play(
            Create(equal),
            Create(math_group)
        )

        self.next_slide(notes="That s where we can make emerge a linear matrix representation")

        line_lenght = 3
        line_width = 24

        

        line_sin_theta = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=TEAL)
        line_cos_theta = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=GOLD)
        line_theta_dot = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=THETA_DOT_COLOR)
        line_theta_dot_sqr = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=MAROON)
        
        lines_matrix = MobjectMatrix(
            [[line_sin_theta,line_cos_theta,line_theta_dot,line_theta_dot_sqr]],
            h_buff=1.2,
            bracket_h_buff=0.3,
        )

        coefficient_matrix = MobjectMatrix(
            [a.generate_target(),b.generate_target(),c.generate_target(),d.generate_target()],
            bracket_h_buff=0.5,
            v_buff=1,
            bracket_v_buff=0.5
        )

        line_theta_ddot = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=THETA_DDOT_COLOR)

        theta_ddot_matrix = MobjectMatrix(
            [line_theta_ddot],
            bracket_h_buff=0.3,
        )

        sindy_system = VGroup(
            lines_matrix,
            times_1.generate_target(),
            coefficient_matrix,
            equal,
            theta_ddot_matrix).arrange(RIGHT,buff=0.5).next_to(catalog_text,DOWN).shift(DOWN*0.2).set_x(0)

        arrow_time = Arrow(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=8,color=DEFAULT_COLOR).next_to(lines_matrix,LEFT,buff=0.1)
        time_text = Text("Time",color=DEFAULT_COLOR).scale(0.5).next_to(arrow_time,LEFT,buff=0.1)
        arrow_time_group = VGroup(arrow_time,time_text)

        self.play(
            Create(arrow_time_group),
            Uncreate(catalog_text),
            FadeOut(axes_sin_theta),
            FadeOut(axes_cos_theta),
            FadeOut(axes_theta_dot_2),
            FadeOut(axes_theta_dot_sqr),
            Uncreate(times_2),
            Uncreate(times_3),
            Uncreate(times_4),
            Uncreate(plus_1),
            Uncreate(plus_2),
            Uncreate(plus_3),
            FadeOut(theta_ddot_axes),
            MoveToTarget(times_1),
            MoveToTarget(a),
            MoveToTarget(b),
            MoveToTarget(c),
            MoveToTarget(d),
            Transform(sin_theta_curve,line_sin_theta),
            Transform(cos_theta_curve,line_cos_theta),
            Transform(theta_dot_2_curve,line_theta_dot),
            Transform(theta_dot_sqr_curve,line_theta_dot_sqr),
            Transform(theta_ddot_curve,line_theta_ddot),
            Create(lines_matrix.get_brackets() ),
            Create(coefficient_matrix.get_brackets() ),
            Create(theta_ddot_matrix.get_brackets() ),
            sin_theta.animate.next_to(line_sin_theta,UP,buff=0.5).scale(1.5),
            cos_theta.animate.next_to(line_cos_theta,UP,buff=0.5).scale(1.5),
            theta_dot.animate.next_to(line_theta_dot,UP,buff=0.5).scale(1.5),
            theta_dot2.animate.next_to(line_theta_dot_sqr,UP,buff=0.5).scale(1.5),
            ddot_theta.animate.next_to(line_theta_ddot,UP,buff=0.5).scale(1.5),
            self.next_slide_number_animation(),
            *[word.animate.set_color(RED_E)  for word in sindy_text_deployed[1:]]
        )

        sindy_system_text = Text("We can define the SINDy linear system",t2c={"linear system":YELLOW_E,"SINDy":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_text_deployed,DOWN,aligned_edge=LEFT)
        self.play(
            Write(sindy_system_text)
        )

        self.next_slide(notes=" Now we can use any linear regression algorithm and more precisely a sparse one")

        target_letter = VGroup(
            MathTex(r"-\frac{g}{L}"),
            MathTex(r"0"),
            MathTex(r"0"),
            MathTex(r"0")
            ).arrange(DOWN,buff=0.5).move_to(coefficient_matrix)

        self.play(
            Transform(a,target_letter[0]),
            Transform(b,target_letter[1]),
            Transform(c,target_letter[2]),
            Transform(d,target_letter[3])
        )

    def construct_sindy_type(self):

        self.next_slide(notes=" # What are the different type of Sindy ?")

        def one_line_title_wrapper(text,i,j):
            return f"\\boldsymbol{{{text}_{{{j+1}}}}}"
        
        def no_title_wrapper(text,i,j):
            return f"\\boldsymbol{{{text}}}"


        classical_sindy_matrix = SindyMatrix(
            [
                [1,1,1,1],
            ],
            title_wrapper=one_line_title_wrapper,
        )

        coefficient_matrix = Matrix(
            [[r"a"],
            [r"b"],
            [r"c"],
            [r"d"]],
        ).scale(0.75)

        force_vector = SindyMatrix(
            [
                [1],
            ],
            base_name=r"F_{ext}",
            title_wrapper=no_title_wrapper,
            reverse_color=True,
        )

        equal = MathTex(r"=").scale(1)

        sindy_equation = VGroup(
            classical_sindy_matrix,
            coefficient_matrix,
            equal,
            force_vector
        ).arrange(RIGHT,buff=0.5)

        self.new_clean_slide("2.1 Sindy type : classic SINDy",contents=sindy_equation,t2c={"SINDy-PI":RED_E})

        self.next_slide(notes="SINDy-PI introduces implicit formulations")

        zero = MathTex(r"0").scale(1).move_to(force_vector.get_contents())

        self.play(
            Transform(force_vector.get_contents(),zero),
            self.next_slide_title_animation("2.2 Sindy type : SINDy-PI",t2c={"SINDy-PI":RED_E}),
            self.next_slide_number_animation()
        )

        subtitle_text = Text("Null space optimization is HARD",t2c={"Null space":RED_E,"HARD":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(self.slide_title,DOWN,aligned_edge=LEFT)

        self.next_slide(notes=" Null space optimization is hard")

        self.play(
            Write(subtitle_text)
        )

        catalog_line = classical_sindy_matrix.get_lines()[0]

        catalog_line.generate_target()

        catalog_line.target[:-1].arrange(RIGHT,buff=0.7).move_to(catalog_line)
        catalog_line.target[-1].move_to(force_vector)

        coefficient_matrix.generate_target()
        coefficient_matrix.target.get_entries()[:-1].arrange(DOWN,buff=0.5).move_to(coefficient_matrix)
        coefficient_matrix.target.get_entries()[-1].set_opacity(0).move_to(coefficient_matrix)

        self.next_slide(notes=" Rearranging catalog line")

        self.play(
            Unwrite(subtitle_text),
            MoveToTarget(catalog_line),
            MoveToTarget(coefficient_matrix),
            FadeOut(force_vector.get_contents())
        )

        # Clean force vector from the zero
        force_vector.remove_matrix_content()



        self.next_slide(notes="What if this contender is not inside our solution ?")

        question_text = Text("What if the right term is not in our catalog ?",t2c={"right term":RED_E,"not":RED_E,"catalog":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_equation,DOWN,aligned_edge=LEFT)

        self.play(
            Write(question_text)
        )

        self.next_slide(notes=" We can try different combination of terms")

        self.play(
            sindy_equation.animate.scale(0.5).to_corner(UR).set_y(0).shift(LEFT*0.25),
            Unwrite(question_text)
        )

        def copy_sindy_equation(copy=True):

            if copy:
                new_sindy_equation = sindy_equation.copy()
            else:
                new_sindy_equation = sindy_equation

            

            new_sindy_equation.generate_target(use_deepcopy=True)

            new_sindy_equation_target = new_sindy_equation.target

            new_lines_matrix_target = new_sindy_equation_target[0]
            new_coefficient_matrix_target = new_sindy_equation_target[1]

            new_catalog_line_target = new_lines_matrix_target.get_lines()[0]
            new_coefficient_target = new_coefficient_matrix_target.get_entries()


            new_lines_matrix = new_sindy_equation[0]
            new_coefficient_matrix = new_sindy_equation[1]

            new_catalog_line = new_lines_matrix.get_lines()[0]
            new_coefficient = new_coefficient_matrix.get_entries()

            return (
                new_sindy_equation,
                new_sindy_equation_target,
                new_catalog_line_target, 
                new_coefficient_target,
                new_catalog_line,
                new_coefficient,
            )
        


        
        # First other group
        new_sindy_equation_1, new_sindy_equation_target_1, new_catalog_line_target_1, new_coefficient_target_1, new_catalog_line_1, new_coefficient_1 = copy_sindy_equation()

        # second other group
        new_sindy_equation_2, new_sindy_equation_target_2, new_catalog_line_target_2, new_coefficient_target_2, new_catalog_line_2, new_coefficient_2 = copy_sindy_equation()

        # third other group
        new_sindy_equation_3, new_sindy_equation_target_3, new_catalog_line_target_3, new_coefficient_target_3, new_catalog_line_3, new_coefficient_3 = copy_sindy_equation()

        # fourth other group
        new_sindy_equation_4, new_sindy_equation_target_4, new_catalog_line_target_4, new_coefficient_target_4, new_catalog_line_4, new_coefficient_4 = copy_sindy_equation(copy=False)
        
        
        # first group - f1,f2,f4 - f3
        new_catalog_line_target_1[3].move_to(new_catalog_line_1[0])
        new_catalog_line_target_1[0].move_to(new_catalog_line_1[3])
        new_coefficient_target_1[3].move_to(new_coefficient_1[0]).set_opacity(1)
        new_coefficient_target_1[0].move_to(new_coefficient_1[3]).set_opacity(0)

        # second group - f1,f4,f3 - f2
        new_catalog_line_target_2[3].move_to(new_catalog_line_2[1])
        new_catalog_line_target_2[1].move_to(new_catalog_line_2[3])
        new_coefficient_target_2[3].move_to(new_coefficient_2[1]).set_opacity(1)
        new_coefficient_target_2[1].move_to(new_coefficient_2[3]).set_opacity(0)

        # third group - f4,f2,f3 - f1
        new_catalog_line_target_3[3].move_to(new_catalog_line_3[2])
        new_catalog_line_target_3[2].move_to(new_catalog_line_3[3])
        new_coefficient_target_3[3].move_to(new_coefficient_3[2]).set_opacity(1)
        new_coefficient_target_3[2].move_to(new_coefficient_3[3]).set_opacity(0)

        # arrange group

        all_sindy_equations = VGroup(
            new_sindy_equation_target_1,
            new_sindy_equation_target_2,
            new_sindy_equation_target_3,
            new_sindy_equation_target_4,
        ).arrange_in_grid(rows=2,cols=2,buff=0.5).next_to(sindy_equation,LEFT)

        

        self.play(
            LaggedStart(
            MoveToTarget(new_sindy_equation_1),
            MoveToTarget(new_sindy_equation_2),
            MoveToTarget(new_sindy_equation_3),
            MoveToTarget(new_sindy_equation_4),
            lag_ratio=0.5)
        )

        all_sindy_equations = VGroup(
            new_sindy_equation_1,
            new_sindy_equation_2,
            new_sindy_equation_3,
            new_sindy_equation_4,
        )

        self.play(
            all_sindy_equations.animate.scale(1.25).next_to(self.slide_title,DOWN).set_x(0),
        )

        self.next_slide(notes=" This is extremely costly in term of time")

        # first group - f1,f2,f4 - f3
        # second group - f1,f4,f3 - f2
        # third group - f4,f2,f3 - f1

        coefficient_1 = new_coefficient_1.copy()
        coefficient_2 = new_coefficient_2.copy()
        coefficient_3 = new_coefficient_3.copy()
        coefficient_4 = new_coefficient_4.copy()

        self.add(coefficient_1,coefficient_2,coefficient_3,coefficient_4)

        classical_sindy_matrix = SindyMatrix(
            [
                [1,1,1,1],
            ],
            title_wrapper=one_line_title_wrapper,
        )

        equal = MathTex(r"=").scale(1)

        coefficient_matrix = Matrix(
            [[r"0",r"{{b}}_{1}",r"{{c}}_{1}",r"{{d}}_{1}"],
            [r"{{a}}_{2}",r"0",r"{{c}}_{2}",r"{{d}}_{2}"],
            [r"{{a}}_{3}",r"{{b}}_{3}",r"0",r"{{d}}_{3}"],
            [r"{{a}}_{4}",r"{{b}}_{4}",r"{{c}}_{4}",r"0"]],
        ).scale(0.75)

        classical_sindy_matrix_2 = SindyMatrix(
            [
                [1,1,1,1],
            ],
            title_wrapper=one_line_title_wrapper,
        )

        sindy_pi_equation = VGroup(
            classical_sindy_matrix.scale(0.75),
            coefficient_matrix,
            equal,
            classical_sindy_matrix_2.scale(0.75),
        ).arrange(RIGHT,buff=0.5)

        self.play(
            FadeOut(all_sindy_equations)
        )

        self.play(
            Create(coefficient_matrix.get_brackets()),
            Write(coefficient_matrix.get_entries()[0]),
            TransformMatchingTex(coefficient_1[1],coefficient_matrix.get_entries()[1]),
            TransformMatchingTex(coefficient_1[2],coefficient_matrix.get_entries()[2]),
            TransformMatchingTex(coefficient_1[3],coefficient_matrix.get_entries()[3]),
            TransformMatchingTex(coefficient_2[0],coefficient_matrix.get_entries()[4]),
            Write(coefficient_matrix.get_entries()[5]),
            TransformMatchingTex(coefficient_2[2],coefficient_matrix.get_entries()[6]),
            TransformMatchingTex(coefficient_2[3],coefficient_matrix.get_entries()[7]),
            TransformMatchingTex(coefficient_3[0],coefficient_matrix.get_entries()[8]),
            TransformMatchingTex(coefficient_3[1],coefficient_matrix.get_entries()[9]),
            Write(coefficient_matrix.get_entries()[10]),
            TransformMatchingTex(coefficient_3[3],coefficient_matrix.get_entries()[11]),
            TransformMatchingTex(coefficient_4[0],coefficient_matrix.get_entries()[12]),
            TransformMatchingTex(coefficient_4[1],coefficient_matrix.get_entries()[13]),
            TransformMatchingTex(coefficient_4[2],coefficient_matrix.get_entries()[14]),
            Write(coefficient_matrix.get_entries()[15]),
        )

        sindy_pi_text = Text("The SINDy-Parallel-Implicit formulation",t2c={"SINDy-Parallel-Implicit":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_pi_equation,DOWN,aligned_edge=LEFT)

        self.play(
            Create(classical_sindy_matrix),
            Create(classical_sindy_matrix_2),
            Write(equal),
            Write(sindy_pi_text)
            )

    def construct(self):

        self.construct_intro()
        self.construct_introduction()
        self.construct_what_is_sindy()
        self.construct_sindy_type()



class WIP(BaseSlide):


    def construct(self):

        self.next_slide(notes=" # What are the different type of Sindy ?")

        def one_line_title_wrapper(text,i,j):
            return f"\\boldsymbol{{{text}_{{{j+1}}}}}"
        
        def no_title_wrapper(text,i,j):
            return f"\\boldsymbol{{{text}}}"


        classical_sindy_matrix = SindyMatrix(
            [
                [1,1,1,1],
            ],
            title_wrapper=one_line_title_wrapper,
        )

        coefficient_matrix = Matrix(
            [[r"a"],
            [r"b"],
            [r"c"],
            [r"d"]],
        ).scale(0.75)

        force_vector = SindyMatrix(
            [
                [1],
            ],
            base_name=r"F_{ext}",
            title_wrapper=no_title_wrapper,
            reverse_color=True,
        )

        equal = MathTex(r"=").scale(1)

        sindy_equation = VGroup(
            classical_sindy_matrix,
            coefficient_matrix,
            equal,
            force_vector
        ).arrange(RIGHT,buff=0.5)

        self.new_clean_slide("2.1 Sindy type : classic SINDy",contents=sindy_equation,t2c={"SINDy-PI":RED_E})

        self.next_slide(notes="SINDy-PI introduces implicit formulations")

        zero = MathTex(r"0").scale(1).move_to(force_vector.get_contents())

        self.play(
            Transform(force_vector.get_contents(),zero),
            self.next_slide_title_animation("2.2 Sindy type : SINDy-PI",t2c={"SINDy-PI":RED_E}),
            self.next_slide_number_animation()
        )

        subtitle_text = Text("Null space optimization is HARD",t2c={"Null space":RED_E,"HARD":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(self.slide_title,DOWN,aligned_edge=LEFT)

        self.next_slide(notes=" Null space optimization is hard")

        self.play(
            Write(subtitle_text)
        )

        catalog_line = classical_sindy_matrix.get_lines()[0]

        catalog_line.generate_target()

        catalog_line.target[:-1].arrange(RIGHT,buff=0.7).move_to(catalog_line)
        catalog_line.target[-1].move_to(force_vector)

        coefficient_matrix.generate_target()
        coefficient_matrix.target.get_entries()[:-1].arrange(DOWN,buff=0.5).move_to(coefficient_matrix)
        coefficient_matrix.target.get_entries()[-1].set_opacity(0).move_to(coefficient_matrix)

        self.next_slide(notes=" Rearranging catalog line")

        self.play(
            Unwrite(subtitle_text),
            MoveToTarget(catalog_line),
            MoveToTarget(coefficient_matrix),
            FadeOut(force_vector.get_contents())
        )

        # Clean force vector from the zero
        force_vector.remove_matrix_content()



        self.next_slide(notes="What if this contender is not inside our solution ?")

        question_text = Text("What if the right term is not in our catalog ?",t2c={"right term":RED_E,"not":RED_E,"catalog":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_equation,DOWN,aligned_edge=LEFT)

        self.play(
            Write(question_text)
        )

        self.next_slide(notes=" We can try different combination of terms")

        self.play(
            sindy_equation.animate.scale(0.5).to_corner(UR).set_y(0).shift(LEFT*0.25),
            Unwrite(question_text)
        )

        def copy_sindy_equation(copy=True):

            if copy:
                new_sindy_equation = sindy_equation.copy()
            else:
                new_sindy_equation = sindy_equation

            

            new_sindy_equation.generate_target(use_deepcopy=True)

            new_sindy_equation_target = new_sindy_equation.target

            new_lines_matrix_target = new_sindy_equation_target[0]
            new_coefficient_matrix_target = new_sindy_equation_target[1]

            new_catalog_line_target = new_lines_matrix_target.get_lines()[0]
            new_coefficient_target = new_coefficient_matrix_target.get_entries()


            new_lines_matrix = new_sindy_equation[0]
            new_coefficient_matrix = new_sindy_equation[1]

            new_catalog_line = new_lines_matrix.get_lines()[0]
            new_coefficient = new_coefficient_matrix.get_entries()

            return (
                new_sindy_equation,
                new_sindy_equation_target,
                new_catalog_line_target, 
                new_coefficient_target,
                new_catalog_line,
                new_coefficient,
            )
        


        
        # First other group
        new_sindy_equation_1, new_sindy_equation_target_1, new_catalog_line_target_1, new_coefficient_target_1, new_catalog_line_1, new_coefficient_1 = copy_sindy_equation()

        # second other group
        new_sindy_equation_2, new_sindy_equation_target_2, new_catalog_line_target_2, new_coefficient_target_2, new_catalog_line_2, new_coefficient_2 = copy_sindy_equation()

        # third other group
        new_sindy_equation_3, new_sindy_equation_target_3, new_catalog_line_target_3, new_coefficient_target_3, new_catalog_line_3, new_coefficient_3 = copy_sindy_equation()

        # fourth other group
        new_sindy_equation_4, new_sindy_equation_target_4, new_catalog_line_target_4, new_coefficient_target_4, new_catalog_line_4, new_coefficient_4 = copy_sindy_equation(copy=False)
        
        
        # first group - f1,f2,f4 - f3
        new_catalog_line_target_1[3].move_to(new_catalog_line_1[0])
        new_catalog_line_target_1[0].move_to(new_catalog_line_1[3])
        new_coefficient_target_1[3].move_to(new_coefficient_1[0]).set_opacity(1)
        new_coefficient_target_1[0].move_to(new_coefficient_1[3]).set_opacity(0)

        # second group - f1,f4,f3 - f2
        new_catalog_line_target_2[3].move_to(new_catalog_line_2[1])
        new_catalog_line_target_2[1].move_to(new_catalog_line_2[3])
        new_coefficient_target_2[3].move_to(new_coefficient_2[1]).set_opacity(1)
        new_coefficient_target_2[1].move_to(new_coefficient_2[3]).set_opacity(0)

        # third group - f4,f2,f3 - f1
        new_catalog_line_target_3[3].move_to(new_catalog_line_3[2])
        new_catalog_line_target_3[2].move_to(new_catalog_line_3[3])
        new_coefficient_target_3[3].move_to(new_coefficient_3[2]).set_opacity(1)
        new_coefficient_target_3[2].move_to(new_coefficient_3[3]).set_opacity(0)

        # arrange group

        all_sindy_equations = VGroup(
            new_sindy_equation_target_1,
            new_sindy_equation_target_2,
            new_sindy_equation_target_3,
            new_sindy_equation_target_4,
        ).arrange_in_grid(rows=2,cols=2,buff=0.5).next_to(sindy_equation,LEFT)

        

        self.play(
            LaggedStart(
            MoveToTarget(new_sindy_equation_1),
            MoveToTarget(new_sindy_equation_2),
            MoveToTarget(new_sindy_equation_3),
            MoveToTarget(new_sindy_equation_4),
            lag_ratio=0.5)
        )

        all_sindy_equations = VGroup(
            new_sindy_equation_1,
            new_sindy_equation_2,
            new_sindy_equation_3,
            new_sindy_equation_4,
        )

        self.play(
            all_sindy_equations.animate.scale(1.25).next_to(self.slide_title,DOWN).set_x(0),
        )

        self.next_slide(notes=" This is extremely costly in term of time")

        # first group - f1,f2,f4 - f3
        # second group - f1,f4,f3 - f2
        # third group - f4,f2,f3 - f1

        coefficient_1 = new_coefficient_1.copy()
        coefficient_2 = new_coefficient_2.copy()
        coefficient_3 = new_coefficient_3.copy()
        coefficient_4 = new_coefficient_4.copy()

        self.add(coefficient_1,coefficient_2,coefficient_3,coefficient_4)

        classical_sindy_matrix = SindyMatrix(
            [
                [1,1,1,1],
            ],
            title_wrapper=one_line_title_wrapper,
        )

        equal = MathTex(r"=").scale(1)

        coefficient_matrix = Matrix(
            [[r"0",r"{{b}}_{1}",r"{{c}}_{1}",r"{{d}}_{1}"],
            [r"{{a}}_{2}",r"0",r"{{c}}_{2}",r"{{d}}_{2}"],
            [r"{{a}}_{3}",r"{{b}}_{3}",r"0",r"{{d}}_{3}"],
            [r"{{a}}_{4}",r"{{b}}_{4}",r"{{c}}_{4}",r"0"]],
        ).scale(0.75)

        classical_sindy_matrix_2 = SindyMatrix(
            [
                [1,1,1,1],
            ],
            title_wrapper=one_line_title_wrapper,
        )

        sindy_pi_equation = VGroup(
            classical_sindy_matrix.scale(0.75),
            coefficient_matrix,
            equal,
            classical_sindy_matrix_2.scale(0.75),
        ).arrange(RIGHT,buff=0.5)

        self.play(
            FadeOut(all_sindy_equations)
        )

        self.play(
            Create(coefficient_matrix.get_brackets()),
            Write(coefficient_matrix.get_entries()[0]),
            TransformMatchingTex(coefficient_1[1],coefficient_matrix.get_entries()[1]),
            TransformMatchingTex(coefficient_1[2],coefficient_matrix.get_entries()[2]),
            TransformMatchingTex(coefficient_1[3],coefficient_matrix.get_entries()[3]),
            TransformMatchingTex(coefficient_2[0],coefficient_matrix.get_entries()[4]),
            Write(coefficient_matrix.get_entries()[5]),
            TransformMatchingTex(coefficient_2[2],coefficient_matrix.get_entries()[6]),
            TransformMatchingTex(coefficient_2[3],coefficient_matrix.get_entries()[7]),
            TransformMatchingTex(coefficient_3[0],coefficient_matrix.get_entries()[8]),
            TransformMatchingTex(coefficient_3[1],coefficient_matrix.get_entries()[9]),
            Write(coefficient_matrix.get_entries()[10]),
            TransformMatchingTex(coefficient_3[3],coefficient_matrix.get_entries()[11]),
            TransformMatchingTex(coefficient_4[0],coefficient_matrix.get_entries()[12]),
            TransformMatchingTex(coefficient_4[1],coefficient_matrix.get_entries()[13]),
            TransformMatchingTex(coefficient_4[2],coefficient_matrix.get_entries()[14]),
            Write(coefficient_matrix.get_entries()[15]),
        )

        sindy_pi_text = Text("The SINDy-Parallel-Implicit formulation",t2c={"SINDy-Parallel-Implicit":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_pi_equation,DOWN,aligned_edge=LEFT)

        self.play(
            Create(classical_sindy_matrix),
            Create(classical_sindy_matrix_2),
            Write(equal),
            Write(sindy_pi_text)
            )




