# import necessary libraries
# wpilib contains useful classes and methods for interfacing with parts of our robot such as sensors and even the driver station
import wpilib

# phoenix5 contains classes and methods to inferface with motors distributed by cross the road electronics
# third party library
import phoenix5

#importing rev libraries for our neo motors
import rev

#IMPORTING OUR COMMANDS
#import our Autonomous
from commands.autonomous import Autonomous

#import our shooting
from commands.auto_shoot import Auto_Shoot

#import our amp 
from commands.auto_amp import Auto_Amp

#import our intake
from commands.auto_intake import Auto_Intake

#IMPORTING OUR SUBSYSTEMS
# import our Drive class that contains various modes of driving and methods for interfacing with our motors
from subsystems.drive import Drive

#import our Shooter class
from subsystems.shooter import Shooter

#import our networking
from subsystems.netowrking import NetworkReceiver

#import our intake class
from subsystems.intake import Intake

#import our climb class
from subsystems.climber import Climber

#import our arm class
from subsystems.arm import Arm

# import our IMU wrapper class with methods to access different values the IMU provides
from subsystems.imu import IMU

#IMPORTING UTILITIES
# import our interpolation function used for joysticks
from utils.math_functions import interpolation_drive

#import our PID function
from utils.pid import PID

# import our constants which serve as "settings" for our robot/code
# mainly IDs for CAN motors, sensors, and our controllers
from utils import constants

# create our base robot class
class MyRobot(wpilib.TimedRobot):
    # initialize timers, motors, and sensors
    # create reference to physical parts of the robot
    def robotInit(self):
        # create an instance of the wpilib.Timer class
        # used for autotonous capabilities
        # for example, because we have a timer, we can move the robot forwards for x amount of seconds
        self.timer = wpilib.Timer()

        # create reference to our Falcon 500 motors
        # each Falcon 500 has a Talon FX motor controller
        # we need to provide each instance of the Talon FX class with its corresponding CAN ID
        # we configured the IDs using the Phoenix Tuner
        self.front_right = phoenix5._ctre.WPI_TalonFX(constants.FRONT_RIGHT_ID)
        self.front_left = phoenix5._ctre.WPI_TalonFX(constants.FRONT_LEFT_ID)
        self.back_left = phoenix5._ctre.WPI_TalonFX(constants.BACK_LEFT_ID)
        self.back_right = phoenix5._ctre.WPI_TalonFX(constants.BACK_RIGHT_ID)

        # invert the motors on the right side of our robot
        self.front_right.setInverted(True)
        self.back_right.setInverted(True)

        #create reference to our Neo motors
        self.shooter_upper_motor = rev.CANSparkMax(constants.SHOOTER_UPPER_MOTOR_ID, rev.CANSparkLowLevel.MotorType.kBrushless)
        self.shooter_lower_motor = rev.CANSparkMax(constants.SHOOTER_LOWER_MOTOR_ID, rev.CANSparkLowLevel.MotorType.kBrushless)

        # create reference to our intake motor
        self.intake_motor = rev.CANSparkMax(constants.INTAKE_MOTOR_ID, rev.CANSparkLowLevel.MotorType.kBrushless)

        #create reference to our climb motors (Falcon 500)
        self.climb_motor_left = phoenix5._ctre.WPI_TalonFX(constants.CLIMB_LEFT_ID)
        self.climb_motor_right = phoenix5._ctre.WPI_TalonFX(constants.CLIMB_RIGHT_ID)

        # create a reference to our IMU
        self.imu_motor_controller = phoenix5._ctre.WPI_TalonSRX(constants.IMU_ID)
        self.imu = IMU(self.imu_motor_controller)

        #reference to the two arm motors that move it up and down
        self.arm_motor_left = phoenix5._ctre.WPI_TalonFX(constants.ARM_LEFT_ID)
        self.arm_motor_right = phoenix5._ctre.WPI_TalonFX(constants.ARM_RIGHT_ID)
        self.imu_arm_controller = phoenix5._ctre.WPI_TalonSRX(constants.ARM_IMU_ID)
        self.arm_imu = IMU(self.imu_arm_controller)

        #REFERENCES/INSTANCES OF THE SUBSYSTEMS
        #instance of the arm class that has methods for moving the arm
        self.arm = Arm(self.arm_motor_left, self.arm_motor_right, self.arm_imu)

        #create an instance of our Intake class that contains methods for shooting
        self.intake = Intake(self.intake_motor)

        #create an instance of our Climb class that contains methods for climbing
        self.climb = Climber(self.climb_motor_left, self.climb_motor_right)

        # create an instance of our Drive class that contains methods for different modes of driving
        self.drive = Drive(self.front_right, self.front_left, self.back_left, self.back_right, self.imu)

        self.networking = NetworkReceiver()
        
        #create an instance of our shooter
        self.shooter = Shooter(self.shooter_upper_motor, self.shooter_lower_motor)

        # create an instance of our controller
        # it is an xbox controller at id constants.CONTROLLER_ID, which is 0
        self.controller = wpilib.XboxController(constants.CONTROLLER_ID)

        # create an instance of our Drive class that contains methods for different modes of driving
        self.drive = Drive(self.front_right, self.front_left, self.back_left, self.back_right, self.imu)
        
        #create an instance of our shooting function
        self.shooter = Shooter(self.shooter_lower_motor, self.shooter_upper_motor)

        #create an instance of our amping function
        self.auto_amp = Auto_Amp(self.arm, self.drive, self.shooter, self.intake, self.imu, self.networking)

        #create an instance for the auto shoot
        self.auto_shoot = Auto_Shoot(self.arm, self.drive, self.shooter, self.intake, self.imu, self.networking)

        #instance for the auto intake
        self.auto_intake = Auto_Intake(self.arm, self.drive, self.intake, self.imu, self.networking)

        # override variables to prevent spinning the same motors in multiple places in the code
        self.drive_override = False

    # setup before our robot transitions to autonomous
    def autonomousInit(self):
        pass

    # ran every 20 ms during autonomous mode
    def autonomousPeriodic(self):
        pass

    # setup before our robot transitions to teleop (where we control with a joystick or custom controller)
    def teleopInit(self):
        pass
        
    # ran every 20 ms during teleop
    def teleopPeriodic(self):
        # test our intake and shooter 2/8 meeting
        if self.controller.getAButton():
            self.intake.intake_spin(1)

        elif self.controller.getBButton():
            self.shooter.shooter_spin(0.7)

        else:
            self.intake.stop()
            self.shooter.stop()

        

        # running drive code
        # check if our drive is not overriden - we are not doing some autonomous task and in this case just want to drive around
        if not self.drive_override:
            # get the x and y axis of the left joystick on our controller
            joystick_x = self.controller.getLeftX()

            # rember that y joystick is inverted
            # multiply by -1
            # "up" on the joystick is -1 and "down" is 1
            joystick_y = self.controller.getLeftY() * -1

            # get the x axis of the right joystick used for turning the robot in place
            joystick_turning = self.controller.getRightX()

            # run field oriented drive based on joystick values
            self.drive.field_oriented_drive(joystick_x, joystick_y, joystick_turning)
            
            # if we click the back button on our controller, reset the "zero" position on the yaw to our current angle
            if self.controller.getBackButton():
                self.imu.reset_yaw()
        # else means that the drive is overriden and in this case want to run autonomous tasks
        else:
            #testing the turning to a certain angle
            if self.controller.getLeftTriggerAxis() == 1:
                self.drive.set_robot_to_angle(90)

            elif self.controller.getRightTriggerAxis() == 1:
                self.drive.set_robot_to_angle(270)

            elif self.controller.getXButton():
                self.drive.set_robot_to_angle(0)

            
        #if the left bumper is pressed, we shoot.
        #if self.controller.getLeftBumperPressed(): self.shoot.autonomous_shoot()
        
        #if the right bumber is pressed, we do the amp
        #if self.controller.getRightBumperPressed(): self.auto_amp.autonomous_amp()

        # print out the joystick values
        # mainly used for debugging where we realized the y axis on the lefy joystick was inverted
        #print(f"getLeftX: {self.controller.getLeftX()}, getLeftY: {self.controller.getLeftY()}, getRightX: {self.controller.getRightX()}, getRightY: {self.controller.getRightY()}")
        
        # print out the left and right triggers to see if they are pressed
        #print(f"left trigger: {self.controller.getLeftTriggerAxis()}, right trigger: {self.controller.getRightTriggerAxis()}")

# run our robot code
if __name__ == "__main__":
    wpilib.run(MyRobot)

# the command that deploys our code to our robot:
#py -3 -m robotpy deploy