import os
import random

import numpy as np
from scipy.integrate import solve_ivp
import math

from manim import *
from manim_slides import Slide

import functools

DEFAULT_COLOR = ManimColor.from_rgb([0.01,0.01,0.01])  # Almost black
DEFAULT_BACKGROUND_COLOR = WHITE

#DEFAULT_COLOR = WHITE
#DEFAULT_BACKGROUND_COLOR = ManimColor.from_rgb([0.01,0.01,0.01])  # Almost white

POSITION_COLOR = RED
VELOCITY_COLOR = GREEN
ACCELERATION_COLOR = BLUE

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
    def new_init(self, *args, substrings_to_isolate=[], fragile_substring = True, **kwargs):
        # Need to report bug to Manim about the substrings_to_isolate creating issue with Tex class (DVI convert)
        # Highly unstable +[r"\ddot{\theta}",r"\dot{\theta}",r"\theta"]
        
        tex_template = TexTemplate()
        tex_template.add_to_preamble(
            r"""
        \usepackage{siunitx}
        \usepackage{amsmath}
        \newcommand{\ts}{\textstyle}
        \newcommand{\qcoordinate}{q}
        """
        )

        if fragile_substring:
            special_substring = [
                r"\ddot{\theta}",
                r"\dot{\theta}",
                r"\theta",
                r"\qcoordinate",
                r"\dot{\qcoordinate}",
                r"\ddot{\qcoordinate}"]
        else:
            special_substring = []
        

        init_func(self, *args, substrings_to_isolate=substrings_to_isolate+special_substring,tex_template=tex_template, **kwargs)

        if fragile_substring:
            self.set_color_by_tex(r"\theta",POSITION_COLOR)
            self.set_color_by_tex(r"\dot{\theta}",VELOCITY_COLOR)
            self.set_color_by_tex(r"\ddot{\theta}",ACCELERATION_COLOR)

            self.set_color_by_tex(r"\qcoordinate",POSITION_COLOR)
            self.set_color_by_tex(r"\dot{\qcoordinate}",VELOCITY_COLOR)
            self.set_color_by_tex(r"\ddot{\qcoordinate}",ACCELERATION_COLOR)

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
SINDY_MATRIX_CLEARANCE = 0.15

class SindyMatrix(VMobject):

    # Matrix of the lines contains Vgroup of the title and the line
    lines= None

    max_height = None
    max_width = None
    
    # Matrix MObjectMatrix
    matrix = None

    # arrow
    arrows = None

    def _default_title_wrapper(text,i,j):
        return f"\\boldsymbol{{{text}_{{{i+1},{j+1}}}}}"

    def __init__(self,unit_matrix,base_name="f",color_matrix=None,title_scale=0.75,fragile_substring=True,title_wrapper=_default_title_wrapper,reverse_color=False,arrow_title=None,**kwargs):
        super().__init__(**kwargs)


        self._create_sindy_matrix(unit_matrix,
                                  base_name=base_name,
                                  color_matrix=color_matrix,
                                  title_wrapper=title_wrapper,
                                  reverse_color=reverse_color,
                                  title_scale=title_scale,
                                  fragile_substring=fragile_substring)

        if arrow_title is not None:

            self.arrows = VGroup()

            for i,title in enumerate(arrow_title):

                self._create_arrow(title,line=i)

            self.add(self.arrows)

    def get_arrows(self):
        return self.arrows

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
    
    def _create_arrow(self,title,line):

        arrow = Arrow(
            start=ORIGIN,
            end=DOWN*self.max_height,
            buff=0.1,
            color=DEFAULT_COLOR
        )

        if title != "":
            title_mob = MathTex(title,color=DEFAULT_COLOR).scale(0.75).next_to(arrow,LEFT,buff=0.1)
        else:
            title_mob = VMobject()

        arrow_group = VGroup(title_mob,arrow)

        arrow_group.next_to(self.matrix,LEFT,buff=0.1).set_y(self.get_lines()[line].get_y())
        #arrow_group.next_to(self.get_lines()[line],LEFT,buff=0.1)
        self.arrows.add(arrow_group)

    def _create_sindy_line(self,color=DEFAULT_COLOR,divide=1,title="",title_scale=0.75,fragile_substring=True,opacity=1):

        #line = Line(start=ORIGIN,end=DOWN*SINDY_LINE_LENGHT/divide+RIGHT*0.01,buff=0,stroke_width=SINDY_LINE_WIDTH,color=color)
        line = RoundedRectangle(height=SINDY_LINE_LENGHT/divide,width=SINDY_LINE_WIDTH,color=color,corner_radius=SINDY_LINE_WIDTH/4)

        if opacity == 0:
            line.set_fill(DEFAULT_BACKGROUND_COLOR,1)
        else:
            line.set_fill(color,1)

        if title != "":
            if opacity == 0:
                title_mob = MathTex(title,color=DEFAULT_BACKGROUND_COLOR,fragile_substring=fragile_substring).scale(title_scale).next_to(line,UP,buff=0.1)
            else:
                title_mob = MathTex(title,color=color,fragile_substring=fragile_substring).scale(title_scale).next_to(line,UP,buff=0.1)
        else:
            title_mob = VMobject()

        height = SINDY_LINE_LENGHT/divide  + title_mob.height 
        width = SINDY_LINE_WIDTH + title_mob.width 

        return VGroup(title_mob,line),(height,width)
    
    def remove_matrix_content(self):

       self.matrix.get_entries().set_opacity(0)
    
    def _create_sindy_matrix(self,unit_matrix,base_name="f",color_matrix=None,title_scale=0.75,fragile_substring=True,title_wrapper=_default_title_wrapper,reverse_color=False):

        color_list = ["BLUE","TEAL","GREEN","GOLD","RED","MAROON","PURPLE"]
        letter_list = ["A","B","C","D","E"]

        rows = len(unit_matrix)
        cols = len(unit_matrix[0])
        if color_matrix is None:
            if rows>=len(letter_list) :
                raise ValueError("Too many rows for letter representation")
            if cols>=len(color_list):
                raise ValueError("Too many columns for color representation")
        
        self.lines = np.zeros((rows,cols),dtype=object)

        max_height = 0
        max_width = 0

        for i in range(len(unit_matrix)):
            for j in range(len(unit_matrix[0])):

                if color_matrix is not None:
                    color = color_matrix[i][j]
                else:
                    color = eval(color_list[ -j-1 if reverse_color else j]+"_"+letter_list[i])

                line,(height,width) = self._create_sindy_line(color=color,divide= rows,title=title_wrapper(base_name,i,j),title_scale=title_scale,fragile_substring=fragile_substring,opacity=unit_matrix[i][j])
                max_height = max(max_height,height)
                max_width = max(max_width,width)
                self.lines[i][j] = line


        self.max_height = max_height
        self.max_width = max_width

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
    "1. What is SINDy",
    "2. SINDy types",
    "3. The Lab SINDy",
    "4. New additions",
    "5. Results",
    "6. Questions and answers",

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

        self.camera.background_color = DEFAULT_BACKGROUND_COLOR 

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

    def next_slide_number_animation(self):
        global global_slide_counter
        global_slide_counter = global_slide_counter + 1

        return self.slide_number.animate(run_time=0.5).set_value(
            global_slide_counter
        )
    
    def next_slide_title_animation(self, title,t2c=None, **kwargs):
        if self.slide_title.text == "":
            self.slide_title = Text(
                title, color=DEFAULT_COLOR, font_size=self.TITLE_FONT_SIZE,t2c={"SINDy":RED_E} if t2c is None else t2c|{"SINDy":RED_E}, **kwargs
            ).to_corner(UL)
            self.add_to_canvas(slide_title=self.slide_title)
            return FadeIn(
                self.slide_title
            )

        else:
            return Transform(
                self.slide_title,
                Text(title, font_size=self.TITLE_FONT_SIZE,t2c={"SINDy":RED_E} if t2c is None else t2c|{"SINDy":RED_E},**kwargs)
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
            self.play(self.next_slide_number_animation(),self.next_slide_title_animation(title,**kwargs))



class Main(BaseSlide):


    def construct_intro(self):

        title = Text(
            "Discovering Nonlinear Dynamics by Simultaneous Lagrangian and Newtonian"
        ).scale(0.5)
        title_2 = Text ("Identification for Implicit and Explicit Sparse Identification").scale(0.5)
        lab_title = Text("Tohoku University - School of engineering - NeuroRobotics Laboratory").scale(0.3)
        author_date = (
            Text("Eymeric Chauchat C4TM1417 - 18th November 2025")
            .scale(0.3)
        )

        intro_group = VGroup(title,title_2,lab_title,author_date).arrange(DOWN)

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

        self.new_clean_slide("1 Introduction",contents=contents)

    def construct_what_is_sindy(self):

        self.next_slide(notes=" # What is SINDy")
        self.new_clean_slide(r"1 What is SINDy")


        pendulum_L = 1

        PendulumObject = Pendulum(theta0=math.pi-0.05,L=pendulum_L,g=15,theta_dot0=.0)


        PendulumOrigin = Dot(radius=0.1,color=BLUE)
        PendulumExtreme = Dot(radius=0.1,color=BLUE).move_to(PendulumOrigin.get_center()).shift(PendulumObject.get_local_vector())

        def get_rod():
            return Line(PendulumOrigin.get_center(),PendulumExtreme.get_center(),color=DEFAULT_COLOR)

        PendulumRod = always_redraw(get_rod)
        PendulumGroup = VGroup(PendulumExtreme,PendulumRod,PendulumOrigin)


        sindy_text = self.slide_title[-5:-1].copy()

        sindy_text_deployed = VGroup(Text("Sparse",t2c={"S":RED_E}),Text("Identification of",t2c={"I":RED_E}),Text("Nonlinear",t2c={"N":RED_E}),Text("Dynamics",t2c={"D":RED_E})).arrange_in_grid(rows=4,cols=1,col_alignments="l").shift(LEFT*3)

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
            new_line = Line(last_line_end,theta_axes.get_origin()+new_point,color=POSITION_COLOR)
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

        theta_dot_curve = theta_dot_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_dot(),line_color=VELOCITY_COLOR,add_vertex_dots=False)

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

        theta_ddot_curve = theta_ddot_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_ddot(),line_color=ACCELERATION_COLOR,add_vertex_dots=False)

        theta_ddot_axes_group = VGroup(theta_ddot_axes,theta_ddot_curve,ddot_theta)
        
        self.play(
            MoveToTarget(ThetaAxesGroup),
            Create(theta_dot_axes),Create(theta_dot_curve),Create(theta_dot_text),
            Create(theta_ddot_axes),Create(theta_ddot_curve),Create(ddot_theta),
        )

        theta_curve_simplified = theta_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas(),line_color=POSITION_COLOR,add_vertex_dots=False)

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

        theta_dot_2_curve = axes_theta_dot_2.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_dot(),line_color=VELOCITY_COLOR,add_vertex_dots=False)

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
        line_theta_dot = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=VELOCITY_COLOR)
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

        line_theta_ddot = Line(start=ORIGIN,end=DOWN*line_lenght,buff=0,stroke_width=line_width,color=ACCELERATION_COLOR)

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

        self.new_clean_slide("2.1 Sindy type : classic SINDy",contents=sindy_equation,t2c={"-PI":RED_E})

        self.next_slide(notes="SINDy-PI introduces implicit formulations")

        zero = MathTex(r"0").scale(1).move_to(force_vector.get_contents())

        self.play(
            Transform(force_vector.get_contents(),zero),
            self.next_slide_title_animation("2.2 Sindy type : SINDy-PI",t2c={"-PI":RED_E}),
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
            [[r"0",r"{{a}}_{2}",r"{{a}}_{3}",r"{{a}}_{4}"],
            [r"{{b}}_{1}",r"0",r"{{b}}_{3}",r"{{b}}_{4}"],
            [r"{{c}}_{1}",r"{{c}}_{2}",r"0",r"{{c}}_{4}"],
            [r"{{d}}_{1}",r"{{d}}_{2}",r"{{d}}_{3}",r"0"]],
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
            TransformMatchingTex(coefficient_2[0],coefficient_matrix.get_entries()[1]),
            TransformMatchingTex(coefficient_3[0],coefficient_matrix.get_entries()[2]),
            TransformMatchingTex(coefficient_4[0],coefficient_matrix.get_entries()[3]),
            TransformMatchingTex(coefficient_1[1],coefficient_matrix.get_entries()[4]),
            Write(coefficient_matrix.get_entries()[5]),
            TransformMatchingTex(coefficient_3[1],coefficient_matrix.get_entries()[6]),
            TransformMatchingTex(coefficient_4[1],coefficient_matrix.get_entries()[7]),
            TransformMatchingTex(coefficient_1[2],coefficient_matrix.get_entries()[8]),
            TransformMatchingTex(coefficient_2[2],coefficient_matrix.get_entries()[9]),
            Write(coefficient_matrix.get_entries()[10]),
            TransformMatchingTex(coefficient_4[2],coefficient_matrix.get_entries()[11]),
            TransformMatchingTex(coefficient_1[3],coefficient_matrix.get_entries()[12]),
            TransformMatchingTex(coefficient_2[3],coefficient_matrix.get_entries()[13]),
            TransformMatchingTex(coefficient_3[3],coefficient_matrix.get_entries()[14]),
            Write(coefficient_matrix.get_entries()[15]),
        )

        sindy_pi_text = Text("The SINDy-Parallel-Implicit formulation",t2c={"SINDy-Parallel-Implicit":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_pi_equation,DOWN,aligned_edge=LEFT)

        self.play(
            Create(classical_sindy_matrix),
            Create(classical_sindy_matrix_2),
            Write(equal),
            Write(sindy_pi_text)
            )
        
        # Addition for the sparsity

        self.next_slide(notes=" Now let's apply our sparse regression algorithm")

        def change_number(entry,new_value):
            return Transform(entry,MathTex(new_value).move_to(entry).scale(0.75)
            )

        self.play(
            change_number(coefficient_matrix.get_entries()[1],"0"),
            change_number(coefficient_matrix.get_entries()[2],"0.3"),
            change_number(coefficient_matrix.get_entries()[3],"0.0"),
            change_number(coefficient_matrix.get_entries()[4],"0.5"),

            change_number(coefficient_matrix.get_entries()[6],"0.3"),
            change_number(coefficient_matrix.get_entries()[7],"2.0"),
            change_number(coefficient_matrix.get_entries()[8],"0.1"),
            change_number(coefficient_matrix.get_entries()[9],"0.0"),

            change_number(coefficient_matrix.get_entries()[11],"0.0"),
            change_number(coefficient_matrix.get_entries()[12],"0.3"),
            change_number(coefficient_matrix.get_entries()[13],"0.5"),
            change_number(coefficient_matrix.get_entries()[14],"0.7"),
        )

        self.next_slide(notes=" Not sparse entry are eliminated")

        lines = classical_sindy_matrix.get_lines()
        lines_2 = classical_sindy_matrix_2.get_lines()

        self.play(
            lines[0][0].animate.set_opacity(0.2),
            lines[0][3].animate.set_opacity(0.2),
            lines_2[0][0].animate.set_opacity(0.2),
            lines_2[0][3].animate.set_opacity(0.2),
            coefficient_matrix.get_entries()[5].animate.set_color(RED_E),
            coefficient_matrix.get_entries()[7].animate.set_color(RED_E),
            coefficient_matrix.get_entries()[13].animate.set_color(RED_E),
            coefficient_matrix.get_entries()[15].animate.set_color(RED_E),

        )

    def construct_sindy_limitation(self):

        self.next_slide(notes=" # The Lab SINDy")

        intro_text = Paragraph(
            "Until now, I showed one coordinate system",
            "But in Newton formulation we have one equation per coordinate"
            ,t2c={"one":RED_E,"per":RED_E},font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)

        catalog_list = MathTex(r"\sin(\qcoordinate)",r",",r"\cos(\qcoordinate)",r",",r"\ddot{\qcoordinate}",r",",r"\dot{\qcoordinate}").next_to(intro_text,DOWN,buff=0.5).set_x(0)

        self.new_clean_slide("3.1 SINDy limitation",contents=VGroup(intro_text,catalog_list))

        catalog_list_1 = MathTex(r"\sin({\qcoordinate}_1{{)}}",r",",r"\cos({\qcoordinate}_1{{)}}",r",",r"\ddot{\qcoordinate}_1",r",",r"\dot{\qcoordinate}_1")
        catalog_list_2 = MathTex(r",",r"\sin({\qcoordinate}_2{{)}}",r",",r"\cos({\qcoordinate}_2{{)}}",r",",r"\ddot{\qcoordinate}_2",r",",r"\dot{\qcoordinate}_2")

        VGroup(catalog_list_1,catalog_list_2).arrange(RIGHT,buff=SMALL_BUFF ).next_to(intro_text,DOWN,buff=1).set_x(0).shift(DOWN*0.5)

        self.next_slide(notes=" Term per term")

        self.play(
            TransformMatchingTex(catalog_list,catalog_list_1),
            TransformMatchingTex(catalog_list.copy(),catalog_list_2)
        )
        self.play(
            VGroup(catalog_list_1,catalog_list_2).animate.arrange(RIGHT,buff=SMALL_BUFF ).next_to(intro_text,DOWN,buff=0.5).set_x(0)
        )

        sin_q1 = catalog_list_1[0:4]
        cos_q1 = catalog_list_1[5:9]
        ddot_q1 = catalog_list_1[10:12]
        dot_q1 = catalog_list_1[13:]

        sin_q2 = catalog_list_2[1:5]
        cos_q2 = catalog_list_2[6:10]
        ddot_q2 = catalog_list_2[11:13]
        dot_q2 = catalog_list_2[14:]

        function_list = [
            sin_q1,
            cos_q1,
            ddot_q1,
            dot_q1,
            sin_q2,
            cos_q2,
            ddot_q2,
            dot_q2,
        ]

        def sqr_format(term):
            """Format a term as squared, e.g., sin(q) -> sin²(q)"""
            return VGroup(term.copy(), MathTex("^2").scale(0.7).next_to(term, RIGHT, buff=0.05,aligned_edge=UP)).set_opacity(0)

        def create_function_couples(function_list):
            """
            Creates all unique couples from function_list.
            For (x, x) pairs, applies sqr_format(x).
            For (x, y) pairs where x != y, creates VGroup(x, y).
            Permutations (x, y) and (y, x) are considered the same.
            """
            couples = VGroup()
            n = len(function_list)
            
            for i in range(n):
                for j in range(i, n):  # Start from i to avoid duplicate permutations
                    if i == j:
                        # Same element: apply sqr_format
                        couples.add(sqr_format(function_list[i]))
                    else:
                        # Different elements: create VGroup
                        couples.add(VGroup(function_list[i].copy(), function_list[j].copy()))
            
            return couples

        
        # Create all couples
        function_couples = create_function_couples(function_list)

        function_couples_target = VGroup(*[couple.generate_target() for couple in function_couples])

        for couple in function_couples_target:
            couple.arrange(RIGHT,buff=0.05).set_opacity(1)

        function_couples_target.arrange_in_grid(rows=6,cols=6,buff=0.2).scale(0.66).next_to(VGroup(catalog_list_1,catalog_list_2),DOWN,buff=0.5).set_x(0)

        self.next_slide(notes=" All the possible couples for an 8 term catalog and a 2 degree polynome")

        self.play(
            LaggedStart(
                *[MoveToTarget(couple) for couple in function_couples[::-1]],
                lag_ratio=0.1
            )
        )
        
        function_couples.generate_target()

        function_couples.target.next_to(intro_text,DOWN,buff=1).set_x(0)

        term_text = Text("This lead to 36 terms to consider for only 8 bases function",t2c={"36 terms": RED_E,"8 bases":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(function_couples.target,DOWN,buff=0.5).set_x(0)

        self.play(
            Unwrite(VGroup(catalog_list_1,catalog_list_2)),
            MoveToTarget(function_couples),
            Write(term_text),
            self.next_slide_number_animation()
        )


        self.next_slide(notes="And we double again when we put everything in the SINDy matrix")

        function_couples_2 = function_couples.copy()

        function_couples_2.generate_target()
        function_couples.generate_target()

        VGroup(function_couples.target,function_couples_2.target).scale(0.5).arrange(DR,buff=0.1).next_to(intro_text,DOWN,buff=1).set_x(0)

        self.play(
            MoveToTarget(function_couples),
            MoveToTarget(function_couples_2),
            Unwrite(term_text)
        )

        self.next_slide(notes=" Finally we can build the SINDy-Newton matrix")

        def sindy_newton_header(text,i,j):

            if j%4==2:
                return r"\boldsymbol{\dotsb}"
            elif j%4==3:
                return r"\boldsymbol{f_{36}}"
            else:
                return f"\\boldsymbol{{{text}_{{{(j%4+1)}}}}}"

        sindy_newton_matrix = SindyMatrix(
            [
                [1,1,1,1,0,0,0,0],
                [0,0,0,0,1,1,1,1],
            ],
            color_matrix=[
                [BLUE_A,TEAL_A,GREEN_A,GOLD_A,0,0,0,0],
                [0,0,0,0,BLUE_B,TEAL_B,GREEN_B,GOLD_B],
            ],
            title_wrapper=sindy_newton_header,
            arrow_title=[r"\textrm{Time} \ {\qcoordinate}_1",r"\textrm{Time} \ {\qcoordinate}_2"],
        ).scale(0.75).next_to(intro_text,DOWN,buff=0.5).set_x(0)

        sindy_newton_lines = sindy_newton_matrix.get_lines()

        first_line = sindy_newton_lines[0][:4]
        second_line = sindy_newton_lines[1][4:]

        self.play(
            Create(sindy_newton_matrix.get_brackets()),
            Create(sindy_newton_matrix.get_arrows()),
            ReplacementTransform(function_couples,first_line),
            ReplacementTransform(function_couples_2,second_line),
        )

    def construct_lagrangian(self):

        self.next_slide(notes=" # The Lab SINDy")

        intro_text = Text("One solution, the lagrangian formulation",t2c={"lagrangian":RED_E},font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)

        lagrangian = intro_text[15:25].copy()

        self.new_clean_slide("3.2 The Lab SINDy introduction",contents=intro_text)

        self.next_slide(notes=" The lagrangian formula")

        lagrangian_formula = MathTex(r"\mathcal{L} = T - V")

        explanation = Text("One equation per system",t2c={"per system":RED_E},font_size=self.CONTENT_FONT_SIZE).scale(0.75).next_to(intro_text,DOWN,buff=0.5,aligned_edge=LEFT)

        extra_text = Text("with T the kinetic energy and V the potential energy",font_size=self.CONTENT_FONT_SIZE).scale(0.5).next_to(lagrangian_formula,DOWN,buff=0.1)

        self.play(Write(explanation),lagrangian.animate.move_to(lagrangian_formula))
        self.play(ReplacementTransform(lagrangian,lagrangian_formula),Write(extra_text))

        self.next_slide(notes=" The Euler-Lagrange equation")

        lagrangian_group = VGroup(lagrangian_formula,extra_text)

        euler_lagrange_1 = MathTex(r"\frac{d}{dt} \left( \frac{\partial \mathcal{L}}{\partial \dot{\qcoordinate}_1} \right) - \frac{\partial \mathcal{L}}{\partial {\qcoordinate}_1} = 0",fragile_substring=False).scale(0.5)
        euler_lagrange_2 = MathTex(r"\frac{d}{dt} \left( \frac{\partial \mathcal{L}}{\partial \dot{\qcoordinate}_2} \right) - \frac{\partial \mathcal{L}}{\partial {\qcoordinate}_2} = 0",fragile_substring=False).scale(0.5)

        euler_lagrange_1[0][9:11].set_color(VELOCITY_COLOR)
        euler_lagrange_1[0][18].set_color(POSITION_COLOR)

        euler_lagrange_2[0][9:11].set_color(VELOCITY_COLOR)
        euler_lagrange_2[0][18].set_color(POSITION_COLOR)

        euler_lagrange_group = VGroup(euler_lagrange_1,euler_lagrange_2).arrange(DOWN,buff=0.2)

        euler_arrow = Arrow(start=ORIGIN,end=DOWN*1,buff=0,color=DEFAULT_COLOR)

        lagrangian_group.generate_target(use_deepcopy=True)
        lagrangian_group.target[0].scale(0.5)


        VGroup(lagrangian_group.target,euler_arrow,euler_lagrange_group).arrange(DOWN,buff=0.2).next_to(explanation,DOWN,buff=0.4).set_x(0)

        euler_text = Text("Euler-Lagrange equation",t2c={"Euler-Lagrange":RED_E},font_size=self.CONTENT_FONT_SIZE).scale(0.75).next_to(euler_arrow,LEFT,buff=0.2)

        self.play(
            MoveToTarget(lagrangian_group),
            Create(euler_arrow),
            Write(euler_text),
            Write(euler_lagrange_group)
        )

        #Debug for color
        #self.add(index_labels(euler_lagrange_1[0],background_stroke_width=0.5,label_height=0.1,background_stroke_color=WHITE))

        lagrange_space_line = Line(start=ORIGIN,end=DOWN*lagrangian_group.height,buff=0.1,color=GREEN).next_to(lagrangian_group,LEFT,buff=0.5)

        newton_space_line = Line(start=ORIGIN,end=DOWN*euler_lagrange_group.height,buff=0.1,color=GREEN).next_to(euler_lagrange_group,LEFT,buff=0.5)

        lagrange_space_text = Text("Lagrange space",t2c={"Lagrange":GREEN},font_size=self.CONTENT_FONT_SIZE).next_to(lagrange_space_line,LEFT,buff=0.2)

        newton_space_text = Text("Newton space",t2c={"Newton":GREEN},font_size=self.CONTENT_FONT_SIZE).next_to(newton_space_line,LEFT,buff=0.2)

        self.next_slide(notes=" From Lagrange to Newton space")

        self.play(
            Create(lagrange_space_line),
            Write(lagrange_space_text),
            Create(newton_space_line),
            Write(newton_space_text)
        )

    def construct_lab_sindy(self):

        self.next_slide(notes=" # The Lab SINDy")

        def lagrangian_term(text,i,j):

            return f"\\boldsymbol{{ \\frac{{d}}{{dt}} \\left( \\frac{{\\partial  {text}_{{{j+1}}} }}{{\\partial \\dot{{\\qcoordinate}}_{{{i+1}}} }} \\right) - \\frac{{\\partial {text}_{{{j+1}}} }}{{\\partial \\qcoordinate_{{{i+1}}} }} }}"

        intro_text=Text("Let's take our catalog function again",font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)

        sindy_lagrangian_matrix = SindyMatrix(
            [
                [1,1,1,1],
                [1,1,1,1],
            ],
            title_wrapper=lagrangian_term,
            title_scale=0.25,
            fragile_substring=False
        ).next_to(intro_text,DOWN,buff=0.6).set_x(0)


        lines = sindy_lagrangian_matrix.get_lines()
        for row in lines:
            for line in row:
                line[0][0].set_color(DEFAULT_COLOR)
                line[0][0][10:12].set_color(VELOCITY_COLOR)
                line[0][0][20].set_color(POSITION_COLOR)
                line[0][0][6:8].set_color(line[1].get_color())
                line[0][0][16:18].set_color(line[1].get_color())
                #self.add(index_labels(line[0][0],background_stroke_width=0.5,label_height=0.1,background_stroke_color=WHITE))

        f_object = VGroup()
        f_persistant = VGroup()

        for i,row in enumerate(lines):
            for j,line in enumerate(row):

                f_1= line[0][0][6:8].set_opacity(0).copy()

                f_1.set_opacity(1).generate_target()
                f_1.move_to(lines[0][j]).scale(3)

                f_2= line[0][0][16:18].set_opacity(0).copy()

                f_2.set_opacity(1).generate_target()
                f_2.move_to(lines[0][j]).scale(3)

                f_object.add( f_1 )
                f_object.add( f_2 )

                if i==0:
                    f_persistant.add( f_1.copy() )
                    f_persistant.add( f_2.copy() )


        f_group = VGroup(f_object,f_persistant)


        self.new_clean_slide("3.3 The Lab SINDy formulation",contents=[intro_text,f_group])        

        self.next_slide(notes=" # The Lab SINDy")

        self.play(
            f_group.animate.next_to(intro_text,DOWN,buff=0.1).set_x(0),
        )

        curved_arrow = CurvedArrow(
            start_point=ORIGIN,
            end_point=UP*(sindy_lagrangian_matrix.get_y()-f_group.get_y()),
            angle=PI/6,
            color=DEFAULT_COLOR
        ).next_to(sindy_lagrangian_matrix,LEFT,buff=0.1).set_y((sindy_lagrangian_matrix.get_y()+f_group.get_y())/2)

        euler_lagrange_text = Text("Euler-Lagrange",t2c={"Euler-Lagrange":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(curved_arrow,LEFT,buff=0.2)


        #Debug for fragile substring manually index the color
        # for row in lines:
        #     for line in row:
        #         self.add(index_labels(line[0][0],background_stroke_width=0.5,label_height=0.1,background_stroke_color=WHITE))

        self.play(
            Create(curved_arrow),
            Write(euler_lagrange_text),
            Create(sindy_lagrangian_matrix.get_brackets())
        )

        self.play(
            LaggedStart(
              *[MoveToTarget(f) for f in f_object]
            ),
            Create(sindy_lagrangian_matrix.get_contents()),
        )

        explanation_text= Text("XL-SINDy formulation, more compact !",t2c={"XL-SINDy":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sindy_lagrangian_matrix,DOWN,aligned_edge=LEFT,buff=0.1)

        self.play(Create(explanation_text))

    def construct_addition_1(self):

        self.next_slide(notes=" # Addition 1")

        def lagrangian_term(text,i,j):
            
            if j < 3:
                return f"\\boldsymbol{{ \\frac{{d}}{{dt}} \\left( \\frac{{\\partial  {text}_{{{j+1}}} }}{{\\partial \\dot{{\\qcoordinate}}_{{{i+1}}} }} \\right) - \\frac{{\\partial {text}_{{{j+1}}} }}{{\\partial \\qcoordinate_{{{i+1}}} }} }}"
            else:
                return r"\boldsymbol{f_4}"
            
        intro_text=Text("How could we have a compact catalog with the advantages of newton ?",t2c={"compact":RED_E,"advantages":RED_E},font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)

        uni_sindy_matrix = SindyMatrix(
            [
                [1,1,1,1,0],
                [1,1,1,0,1],
            ],
            title_wrapper=lagrangian_term,
            title_scale=0.25,
            fragile_substring=False
        ).next_to(intro_text,DOWN,buff=0.5).set_x(0)

        lagrange_line= VGroup()
        newton_line= VGroup()


        uni_sindy_lines = uni_sindy_matrix.get_lines()
        for row in uni_sindy_lines:
            for j,line in enumerate(row):

                

                if j < 3:
                    line[0][0].set_color(DEFAULT_COLOR)
                    line[0][0][10:12].set_color(VELOCITY_COLOR)
                    line[0][0][20].set_color(POSITION_COLOR)
                    line[0][0][6:8].set_color(line[1].get_color())
                    line[0][0][16:18].set_color(line[1].get_color())
                    
                    lagrange_line.add(line)
                else:
                    newton_line.add(line)

                line.generate_target()

                #Debug for color
                #self.add(index_labels(line[0][0],background_stroke_width=0.5,label_height=0.1,background_stroke_color=WHITE))


        bracket_left,bracket_right = uni_sindy_matrix.get_brackets()

        bracket_left.generate_target()
        bracket_right.generate_target()

        fake_bracket_left = bracket_left.copy()
        fake_bracket_right = bracket_right.copy()

        bi_matrix = VGroup(VGroup(
            bracket_left,
            lagrange_line,
            fake_bracket_right).arrange(RIGHT,buff=SINDY_MATRIX_CLEARANCE*2),
            VGroup(
            fake_bracket_left,
            newton_line,
            bracket_right,
        ).arrange(RIGHT,buff=SINDY_MATRIX_CLEARANCE*2)
        ).arrange(RIGHT,buff=1).next_to(intro_text,DOWN,buff=0.5).set_x(0)

        self.new_clean_slide("4.1 First addition",contents=[intro_text,bi_matrix])

        self.next_slide(notes=" The lagrangian formula")

        self.play(
            FadeOut(fake_bracket_left),
            FadeOut(fake_bracket_right),
        )

        explanation_text= Text("An unified Lagrange-Newton SINDy matrix",t2c={"Lagrange-Newton":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(bi_matrix,DOWN,aligned_edge=LEFT,buff=0.1)

        self.play(
            MoveToTarget(bracket_left),
            MoveToTarget(bracket_right),
            *[MoveToTarget(line) for line in lagrange_line],
            *[MoveToTarget(line) for line in newton_line],
            Write(explanation_text)
            )

    def construct_addition_2(self):

        self.next_slide(notes=" # Addition 2")

        extra_description_text= Text("How can we guess implicit and explicit in complex system ?",t2c={"complex":RED_E,"implicit":RED_E,"explicit":RED_E},font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)

        complex_sindy_matrix = SindyMatrix(
            [
                [1,0,0,0,0],
                [0,1,1,0,1],
                [0,1,0,1,0]
            ],
            arrow_title=[r"\textrm{Time} \ {\qcoordinate}_1",r"\textrm{Time} \ {\qcoordinate}_2",r"\textrm{Time} \ {\qcoordinate}_3"],
        )

        def forces_header(text,i,j):
            return f"\\boldsymbol{{ {text}_{{{i+1}}} }}"

        forces_matrix = SindyMatrix(
            [
                [0],
                [0],
                [1],
            ],
            title_wrapper=forces_header,
            base_name=r"{F_{ext}}",
            reverse_color=True,
        )

        coefficient = MathTex(r"\Xi").scale(1)

        equal = MathTex(r"=").scale(1)

        sindy_equation = VGroup(
            complex_sindy_matrix,
            coefficient,
            equal,
            forces_matrix
        ).arrange(RIGHT,buff=0.5).scale(0.75).next_to(extra_description_text,DOWN,buff=0.5).set_x(0)

        self.new_clean_slide("4.2 Second addition",contents=[extra_description_text,sindy_equation])

        sindy_equation.generate_target()

        first_step = Text("1. Where are external forces ?",t2c={"external forces":RED_E},font_size=self.CONTENT_FONT_SIZE)
        second_step = Text("2. What functions are activated ?",t2c={"activated":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(first_step,DOWN,aligned_edge=LEFT,buff=0.5)
        third_step = Text("3. What coordinate activate these functions ? ",t2c={"coordinate":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(second_step,DOWN,aligned_edge=LEFT,buff=0.5)
        fourth_step = Text("4. Loop until no more discovery",t2c={"no more discovery":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(third_step,DOWN,aligned_edge=LEFT,buff=0.5)
        fifth_step = Text("5. Execute SINDy on this sub-system",t2c={"SINDy":RED_E,"sub-system":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(fourth_step,DOWN,aligned_edge=LEFT,buff=0.5)
        sixth_step = Text("6. Execute SINDy-PI on non-discovered coordinate",t2c={"SINDy-PI":RED_E,"non-discovered":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(fifth_step,DOWN,aligned_edge=LEFT,buff=0.5)
        seventh_step = Text("7. Combine everything",t2c={"Combine":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(sixth_step,DOWN,aligned_edge=LEFT,buff=0.5)


        text_group = VGroup(
            first_step,
            second_step,
            third_step,
            fourth_step,
            fifth_step,
            sixth_step,
            seventh_step
        ).scale(0.75).next_to(sindy_equation.target,RIGHT,buff=0.2)

        explanation_group = VGroup(sindy_equation.target,text_group)
        explanation_group.scale(0.8).next_to(extra_description_text,DOWN,buff=0.5).set_x(0)

        self.next_slide(notes=" I will explain the algorithm, first we isolate external forces")
        
        self.play(
            MoveToTarget(sindy_equation),
        )

        complex_sindy_matrix_lines = complex_sindy_matrix.get_lines()
        forces_matrix_lines = forces_matrix.get_lines()

        DIM_OPACITY = 0.1

        self.play(
            Write(first_step),
            forces_matrix_lines[0].animate.set_opacity(DIM_OPACITY),
            forces_matrix_lines[1].animate.set_opacity(DIM_OPACITY),
            complex_sindy_matrix_lines.animate.set_opacity(DIM_OPACITY)
        )

        self.next_slide(notes=" Second we propagate on the left side")

        self.play(
            Write(second_step),
            complex_sindy_matrix_lines[2].animate.set_opacity(1)
        )

        self.next_slide(notes=" Second and half we propagathe the function")

        self.play(
            complex_sindy_matrix_lines[1][1].animate.set_opacity(1)
        )

        self.next_slide(notes=" Third propagate to the coordinate")

        self.play(
            Write(third_step),
            complex_sindy_matrix_lines[1].animate.set_opacity(1),
            forces_matrix_lines[1].animate.set_opacity(1)
        )

        self.next_slide(notes=" Fourth loop")

        self.play(
            Write(fourth_step),
        )

        self.next_slide(notes=" Fifth execute SINDy")

        complex_sindy_matrix_lines.generate_target(use_deepcopy=True).set_opacity(DIM_OPACITY)
        complex_sindy_matrix_lines.target[2][3].set_opacity(1)

        self.play(
            Write(fifth_step),
            MoveToTarget(complex_sindy_matrix_lines),
            forces_matrix_lines.animate.set_opacity(DIM_OPACITY)
        )

        self.next_slide(notes=" Sixth execute SINDy-PI on non discovered coordinate")

        self.play(
            Write(sixth_step),
            complex_sindy_matrix_lines[0].animate.set_opacity(1),
            complex_sindy_matrix_lines[1].animate.set_opacity(1),
            complex_sindy_matrix_lines[2].animate.set_opacity(DIM_OPACITY)
        )

        self.next_slide(notes=" Seventh combine everything")

        complex_sindy_matrix_lines.generate_target(use_deepcopy=True).set_opacity(DIM_OPACITY)
        complex_sindy_matrix_lines.target[0][0].set_opacity(1)
        complex_sindy_matrix_lines.target[1][4].set_opacity(1)
        complex_sindy_matrix_lines.target[2][3].set_opacity(1)

        self.play(
            Write(seventh_step),
            MoveToTarget(complex_sindy_matrix_lines)
        )

    def construct_result_protocol(self):

        self.next_slide(notes=" # Result")

        intro_text = Text("Test protocol has been established to evaluate the performance of the algorithm",font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)

        image_double_pendulum = ImageMobject("image/double_pendulum.png")
        double_pendulum_text= Text("Double Pendulum",t2c={"Double Pendulum":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(image_double_pendulum,DOWN,buff=0.1)

        image_cartpole = ImageMobject("image/cartpole.png").scale_to_fit_height(image_double_pendulum.height)
        cartpole_text= Text("Cartpole",t2c={"Cartpole":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(image_cartpole,DOWN,buff=0.1)

        image_double_cartpole = ImageMobject("image/double_cartpole.png").scale_to_fit_height(image_double_pendulum.height)
        double_cartpole_text= Text("Double Cartpole",t2c={"Double Cartpole":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(image_double_cartpole,DOWN,buff=0.1)

        image_group = Group(
            Group(image_double_pendulum,double_pendulum_text),
            Group(image_cartpole,cartpole_text),
            Group(image_double_cartpole,double_cartpole_text)
        ).arrange(RIGHT,buff=1).scale(0.5)

        


        self.new_clean_slide("5.1 Result gathering",contents=[intro_text,image_group])

        self.next_slide(notes=" let's take example of double cartpole")

        double_cartpole_group = Group(image_double_cartpole,double_cartpole_text)
        double_cartpole_group.generate_target()

        double_cartpole_group.target.scale(0.5)

        force_input = ImageMobject("image/force_input.png").scale(0.25)

        result_image = ImageMobject("image/result_comparison.png").scale(0.25)

        system_box = Rectangle(color=YELLOW_E,height=2,width=3)
        input_arrow = Arrow(start=system_box.get_left()+LEFT*3,end=system_box.get_left(),buff=0.0)
        output_arrow = Arrow(start=system_box.get_right(),end=system_box.get_right()+RIGHT*3,buff=0.0)
        system_label = Text("System",color=YELLOW_E).move_to(system_box.get_center())

        input_label = MathTex(r"\qcoordinate,\dots , \dot{\qcoordinate},\dots").next_to(input_arrow,UP)
        output_label = MathTex(r"\ddot{\qcoordinate},\dots").next_to(output_arrow,UP)

        system = VGroup(system_box,input_arrow,output_arrow,system_label,input_label,output_label).scale(0.33).next_to(double_cartpole_group,RIGHT,buff=0.5)

        Group(force_input,result_image,double_cartpole_group.target,system).scale(1.33).arrange_in_grid(cols=2,rows=2,buff=1).next_to(intro_text,DOWN,buff=0.5).set_x(0)
        force_input_text = Text("Force input",t2c={"Force input":RED_E},font_size=self.CONTENT_FONT_SIZE).scale(0.66).next_to(force_input,DOWN,buff=0.1)
        result_text = Text("Comparison between real and discovered",t2c={"real":RED_E,"discovered":RED_E},font_size=self.CONTENT_FONT_SIZE).scale(0.66).next_to(result_image,DOWN,buff=0.1)

        function_arrow = CurvedArrow(
            end_point=double_cartpole_group.target.get_left()+LEFT*0.2,
            start_point=force_input.get_left()+LEFT*0.2,
            angle=PI/3,
            color=DEFAULT_COLOR
        )

        self.play(
            FadeOut(Group(image_double_pendulum,double_pendulum_text,image_cartpole,cartpole_text)),
        )

        self.play(
            MoveToTarget(double_cartpole_group),
            FadeIn(force_input),
            Create(function_arrow),
            Write(force_input_text)
        )

        self.next_slide(notes="Create a system from the data gathered")

        function_arrow_2 = CurvedArrow(
            end_point=system.get_bottom()+DOWN*0.2,
            start_point=double_cartpole_group.get_bottom()+DOWN*0.2,
            angle=PI/3,
            color=DEFAULT_COLOR
        )

        self.play(
            Create(function_arrow_2),
            Create(system)
        )

        self.next_slide(notes=" compare real system and discovered system")

        function_arrow_3 = CurvedArrow(
            end_point=result_image.get_right()+RIGHT*0.2,
            start_point=system.get_right()+RIGHT*0.2,
            angle=PI/3,
            color=DEFAULT_COLOR
        )

        self.play(  
            Create(function_arrow_3),
            FadeIn(result_image),
            Write(result_text)
        )

    def construct_result(self):

        self.next_slide(notes=" # Result")


        intro_text_1 = Text("SINDy-PI vs SINDy vs Mixed SINDy has been compared on",t2c={"-PI":RED_E,"SINDy":RED_E,"Mixed":RED_E},font_size=self.CONTENT_FONT_SIZE).to_corner(UL).shift(DOWN*1)
        intro_text_2 = Text("3 systems,3 levels of damping and every combinaison of implicit explicit",t2c={"3":RED_E,"every combinaison":RED_E},font_size=self.CONTENT_FONT_SIZE).next_to(intro_text_1,DOWN,buff=0.1,aligned_edge=LEFT)


        self.new_clean_slide("5.2 Result table",contents=[  intro_text_1,intro_text_2])

        table = Tex(r"""
\small
\begin{tabular}{lrrrrrrrr}
\hline
combo type & invalid & timeout & uncompleted & 1st & 2nd & 2nd$>$ & Wins WC & success rate \\
\hline
mixed x mixed (our) & 25 & 0 & 20 & 59 & 12 & 0 & 45 & 0.61 \\
mixed x explicit (our) & 14 & 0 & 17 & 53 & 8 & 0 & 42 & 0.66 \\
sindy x mixed & 81 & 43 & 11 & 12 & 8 & 0 & 3 & 0.18 \\
sindy x explicit & 61 & 16 & 11 & 12 & 8 & 0 & 3 & 0.22 \\
mixed x implicit (our)& 1 & 0 & 1 & 10 & 2 & 2 & 6 & 0.88 \\
xlsindy x mixed & 59 & 0 & 43 & 3 & 6 & 4 & 3 & 0.11 \\
xlsindy x explicit & 38 & 0 & 43 & 3 & 3 & 5 & 3 & 0.12 \\
xlsindy x implicit & 0 & 0 & 1 & 2 & 1 & 1 & 0 & 0.80 \\
sindy x implicit & 24 & 23 & 0 & 0 & 0 & 0 & 0 & 0.00 \\
\hline
\end{tabular}
""").scale(0.5).next_to(intro_text_2,DOWN,buff=0.5).set_x(0)

        self.next_slide(notes=" Table of results")

        self.play(
            Write(table)
        )

    def construct_conclusion(self):

        self.next_slide(notes=" # Conclusion")

        conclusion_paragraph = Paragraph(
            "Unified SINDy enables the use of more compact catalogs,",
            "keep the advantages of both Newton and Lagrange formulation,",
            "open the door to complex system identification.",
            "Real world mixed implicit and explicit systems can also be identified",
            t2c={"Unified SINDy":RED_E,"Newton":RED_E,"Lagrange":RED_E,"complex":RED_E,"real world":RED_E},
            font_size=self.CONTENT_FONT_SIZE
        ).align_to(self.UL,LEFT).shift(RIGHT*1)

        self.new_clean_slide("6 Conclusion",contents=conclusion_paragraph)

    def construct_qa(self):

        self.next_slide(notes=" # QA")

        main_library_text = Text("Main library can be found here :",font_size=self.CONTENT_FONT_SIZE)

        main_library_link = Text("github.com/Eymeric65/py-xl-sindy",t2c={"github.com/Eymeric65/py-xl-sindy":BLUE_E},font_size=self.CONTENT_FONT_SIZE).next_to(main_library_text,DOWN,buff=0.1)

        auxiliary_content = Text("Presentation slide code, experiment data, batch generation code can be found here :",font_size=self.CONTENT_FONT_SIZE).next_to(main_library_link,DOWN,buff=0.5)
        auxiliary_content_link = Text("github.com/Eymeric65/py-xl-sindy-data-visualisation",t2c={"github.com/Eymeric65/py-xl-sindy-data-visualisation":BLUE_E},font_size=self.CONTENT_FONT_SIZE).next_to(auxiliary_content,DOWN,buff=0.1)

        live_demo_text = Text("Experiment visualisation website can be found here :",font_size=self.CONTENT_FONT_SIZE).next_to(auxiliary_content_link,DOWN,buff=0.5)
        live_demo_link = Text("eymeric65.github.io/py-xl-sindy-data-visualisation/",t2c={"eymeric65.github.io/py-xl-sindy-data-visualisation/":BLUE_E},font_size=self.CONTENT_FONT_SIZE).next_to(live_demo_text,DOWN,buff=0.1)

        content_group = VGroup(
            main_library_text,
            main_library_link,
            auxiliary_content,
            auxiliary_content_link,
            live_demo_text,
            live_demo_link
        ).move_to(ORIGIN)

        self.new_clean_slide("7 Questions and answers",contents=content_group)

    def construct(self):

        self.construct_intro()
        #self.construct_introduction()
        self.construct_what_is_sindy()
        self.construct_sindy_type()
        self.construct_sindy_limitation()
        self.construct_lagrangian()
        self.construct_lab_sindy() # 8mn until here
        self.construct_addition_1() # 9mn until here
        self.construct_addition_2() # 11mn until here (probable)
        self.construct_result_protocol() # 12mn until here
        self.construct_result() # 13mn until here
        self.construct_conclusion() # 14mn until here
        self.construct_qa() # 15mn until here



class WIP(BaseSlide):

    def construct(self):

        pass



        

        
        






        













