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
    
    def next_slide_title_animation(self, title):
        if self.slide_title.text == "":
            self.slide_title = Text(
                title, color=DEFAULT_COLOR, font_size=self.TITLE_FONT_SIZE
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
    
    def new_clean_slide(self, title, contents=None):

        self.play(
            self.next_slide_number_animation(),
            self.next_slide_title_animation(title),
            self.wipe(
                self.mobjects_without_canvas if self.mobjects_without_canvas else [],
                contents if contents else [],
                return_animation=True,
            ),
        )



class Main(BaseSlide):


    def construct_intro(self):

        title = Text(
            "Unified framowork for SINDy"
        ).scale(0.5)
        author_date = (
            Text("Eymeric Chauchat - 18th November 2025")
            .scale(0.3)
            .next_to(title, DOWN)
        )

        self.play(
            self.next_slide_number_animation(),
            FadeIn(title), 
            FadeIn(author_date)
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

    def construct(self):

        self.construct_intro()

        

class WIP(BaseSlide):


    def construct(self):


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

        pendulum_L = 1

        PendulumObject = Pendulum(theta0=math.pi-0.03,L=pendulum_L,g=15,theta_dot0=.0)


        PendulumOrigin = Dot(radius=0.1,color=BLUE)
        PendulumExtreme = Dot(radius=0.1,color=BLUE).move_to(PendulumOrigin.get_center()).shift(PendulumObject.get_local_vector())

        def get_rod():
            return Line(PendulumOrigin.get_center(),PendulumExtreme.get_center(),color=DEFAULT_COLOR)

        PendulumRod = always_redraw(get_rod)
        PendulumGroup = VGroup(PendulumExtreme,PendulumRod,PendulumOrigin)

        contents = [PendulumGroup]

        self.next_slide(notes=" # What is SINDy")
        self.new_clean_slide("1.2 What is SINDy",contents=contents)

        self.next_slide(notes=" Our pendulum is govern by equation following a paradigm")

        newton_equation = MathTex(r"F \left( \theta , \dot{\theta} \right)",r"=", r"m \ddot{\theta} ").shift(RIGHT*2)

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

        self.wait(4*PendulumObject.get_period(),stop_condition=lambda: (PendulumObject.get_theta() > math.pi-0.05) and (PendulumObject.get_time()>3) )

        PendulumObject.deactivate()
        PendulumExtreme.remove_updater(update_pendulum)
        PendulumRod.remove_updater(update_rod)

        self.next_slide(notes=" Let's analyze the data of our pendulum")

        PendulumGroup.generate_target()
        PendulumGroup.target.to_edge(UL).shift(RIGHT*pendulum_L+DOWN*pendulum_L)

        self.play(
            ode_equation.animate.move_to(PendulumGroup.target.get_center()).align_to(self.UR,RIGHT).shift(LEFT*0.5),
            MoveToTarget(PendulumGroup),
            )

        simulation_time=10

        x_scale = 0.5
        y_scale = 0.5

        axes = Axes(
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
        )
        axes.shift(PendulumOrigin.get_center()- axes.get_origin() +RIGHT*(pendulum_L+0.5))

        axes_label= axes.get_axis_labels(
            x_label=Tex("Time (s)",color=DEFAULT_COLOR).scale(0.5),
            y_label=MathTex(r"\theta \mathrm{(rad)}",color=DEFAULT_COLOR).scale(0.5),
        )

        # The curve that will be traced when pendulum moves
        theta_curve = VGroup()
        PendulumObject.reset_time()
        curve_start = axes.get_origin()+np.array([x_scale*PendulumObject.get_time(), PendulumObject.get_theta()/math.pi*y_scale, 0])

        theta_curve.add(Line(curve_start,curve_start))

        def get_curve():
            if PendulumObject.is_active() == False:
                return theta_curve
            
            last_line_end = theta_curve[-1].get_end()
            new_point = np.array([x_scale*PendulumObject.get_time(), PendulumObject.get_theta()/math.pi*y_scale, 0])
            new_line = Line(last_line_end,axes.get_origin()+new_point,color=THETA_COLOR)
            theta_curve.add(new_line)
            return theta_curve
        
        self.play(Create(axes),Create(axes_label))

        PendulumObject.activate()
        PendulumExtreme.add_updater(update_pendulum)
        PendulumRod.add_updater(update_rod)
        
        ThetaCurve = always_redraw(get_curve)

        self.add(ThetaCurve)
        self.wait(simulation_time,stop_condition=lambda: PendulumObject.get_time()>=simulation_time )

        PendulumObject.deactivate()
        PendulumExtreme.remove_updater(update_pendulum)
        PendulumRod.remove_updater(update_rod)

        ThetaAxesGroup = VGroup(axes,axes_label,ThetaCurve)

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
        ).next_to(ThetaAxesGroup.target,DOWN,0.5,LEFT)

        theta_dot_axes_label= theta_dot_axes.get_axis_labels(
            x_label=Tex("Time (s)",color=DEFAULT_COLOR).scale(0.5),
            y_label=MathTex(r"\dot{\theta} \mathrm{(rad/s)}",color=DEFAULT_COLOR).scale(0.5),
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
        ).next_to(theta_dot_axes,DOWN,0.5,LEFT)

        theta_ddot_axes_label= theta_ddot_axes.get_axis_labels(
            x_label=Tex("Time (s)",color=DEFAULT_COLOR).scale(0.5),
            y_label=MathTex(r"\ddot{\theta} \mathrm{(rad/s^2)}",color=DEFAULT_COLOR).scale(0.5),
        )

        theta_ddot_curve = theta_ddot_axes.plot_line_graph(PendulumObject.get_times(),PendulumObject.get_thetas_ddot(),line_color=THETA_DDOT_COLOR,add_vertex_dots=False)

        self.play(
            MoveToTarget(ThetaAxesGroup),
            Create(theta_dot_axes),Create(theta_dot_curve),Create(theta_dot_axes_label),
            Create(theta_ddot_axes),Create(theta_ddot_curve),Create(theta_ddot_axes_label),
        )

        self.next_slide(notes=" We have now all the data to perform SINDy")

        self.play(
            FadeOut(PendulumGroup),
            FadeOut(ode_equation),
            VGroup(
                ThetaAxesGroup,
                theta_dot_axes,
                theta_dot_curve,
                theta_dot_axes_label,
                theta_ddot_axes,
                theta_ddot_curve,
                theta_ddot_axes_label,
            ).animate.scale(0.5).to_corner(UR),
            self.next_slide_number_animation()
        )

        self.next_slide(notes="Let's get back to our paradigm newton")

        newton_equation = MathTex(r"F \left( \theta , \dot{\theta} \right)",r"=", r"m \ddot{\theta} ")

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

        system_box = Rectangle(color=YELLOW,height=2,width=3)
        input_arrow = Arrow(start=system_box.get_left()+LEFT*3,end=system_box.get_left(),buff=0.0)
        output_arrow = Arrow(start=system_box.get_right(),end=system_box.get_right()+RIGHT*3,buff=0.0)
        system_label = Text("System").move_to(system_box.get_center())

        input_label = MathTex(r"\theta , \dot{\theta}").next_to(input_arrow,UP)
        output_label = MathTex(r"\ddot{\theta}").next_to(output_arrow,UP)

        system = VGroup(system_box,input_arrow,output_arrow,system_label,input_label,output_label)

        # Until now 1mn from the start of the construct

        self.play(
            FadeOut(other_term),
            Transform(VGroup(force_term,force_equation_box),system)
        )







