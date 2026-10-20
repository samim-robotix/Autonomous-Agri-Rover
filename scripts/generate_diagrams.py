"""
Script to generate ultra-high-resolution, publication-grade PNG diagrams
for Agriculture Rover System Architecture and Autonomous Workflow Pipeline.
Solid lines and clean robotics engineering aesthetics.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("assets", exist_ok=True)

def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    fig.patch.set_facecolor('#0B0F19')
    ax.set_facecolor('#0B0F19')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 96, "AGRICULTURE ROVER - SYSTEM HARDWARE & SOFTWARE ARCHITECTURE", 
            color='#00FFCC', fontsize=18, fontweight='bold', ha='center', fontfamily='sans-serif')
    ax.text(50, 93, "High-Throughput Vision-Based Navigation & Active Targeted Spraying (Pure Python + Edge AI + Microcontroller)", 
            color='#94A3B8', fontsize=10, ha='center', fontfamily='sans-serif')

    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color, text_color='#FFFFFF', sub_color='#94A3B8'):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=1.2",
                                     facecolor=bg_color, edgecolor=border_color, linewidth=2.0)
        ax.add_patch(box)
        if title:
            ax.text(x + w/2, y + h - 2.8, title, color=text_color, fontsize=10, fontweight='bold', ha='center')
        if subtitle:
            ax.text(x + w/2, y + h/2 - 0.5, subtitle, color=sub_color, fontsize=8.5, ha='center', va='center')

    def draw_solid_arrow(x1, y1, x2, y2, color='#38BDF8', label=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2, mutation_scale=16))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 1.2, label, color='#F8FAFC', fontsize=8, fontweight='bold', ha='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='#1E293B', edgecolor=color, lw=1))

    # SECTION 1: PHYSICAL HARDWARE LAYER (Bottom)
    draw_box(4, 4, 92, 18, "LAYER 1: PHYSICAL HARDWARE, SENSORS & ACTUATORS", "", '#111827', '#1E293B', '#38BDF8')
    draw_box(6, 6, 16, 12, "6 DC Motors", "Rocker-Bogie Chassis\nSkid-Steer 6WD", '#1F2937', '#3B82F6')
    draw_box(24, 6, 15, 12, "HC-SR04", "Ultrasonic Distance\nTrigger & Echo", '#1F2937', '#10B981')
    draw_box(41, 6, 16, 12, "Pan Servo", "MG996R Metal Gear\n0°-180° Sweep", '#1F2937', '#F59E0B')
    draw_box(59, 6, 16, 12, "12V Pump & Relay", "Diaphragm Sprayer\nOpto-isolated Relay", '#1F2937', '#EF4444')
    draw_box(77, 6, 17, 12, "USB Web Camera", "Wide-Angle Lens\n1080p / 30 FPS", '#1F2937', '#8B5CF6')

    # SECTION 2: EMBEDDED CONTROLLER LAYER
    draw_box(4, 28, 65, 18, "LAYER 2: LOW-LEVEL EMBEDDED FIRMWARE (Arduino / ESP32)", "", '#111827', '#1E293B', '#10B981')
    draw_box(7, 30, 18, 12, "Motor PWM Driver", "Pins D2,D3,D4,D5,D6,D7\nH-Bridge Direction/PWM", '#1E293B', '#3B82F6')
    draw_box(27, 30, 18, 12, "Ultrasonic & Watchdog", "Non-blocking Ping\n1500ms Serial Watchdog", '#1E293B', '#10B981')
    draw_box(47, 30, 20, 12, "Actuator Timers", "Servo PWM Pin D9\nTimed Spray Relay D8", '#1E293B', '#F59E0B')

    # Direct arrows from Layer 1 to Layer 2
    draw_solid_arrow(14, 28, 14, 18, '#3B82F6', 'PWM / DIR')
    draw_solid_arrow(31, 18, 31, 28, '#10B981', 'Echo Pulse')
    draw_solid_arrow(49, 28, 49, 18, '#F59E0B', 'Servo PWM')
    draw_solid_arrow(66, 28, 66, 18, '#EF4444', 'Relay Trigger')

    # SECTION 3: COMMUNICATION BUS
    draw_box(20, 52, 35, 8, "BIDIRECTIONAL UART SERIAL INTERFACE", "115200 Baud | JSON-free Low Overhead ASCII Packets | Telemetry Streaming", '#0F172A', '#38BDF8', '#38BDF8')
    draw_solid_arrow(36, 46, 36, 52, '#38BDF8', 'Telemetry (Dist, Angles, State)')
    draw_solid_arrow(39, 60, 39, 46, '#38BDF8', 'Commands (MOVE, SERVO, SPRAY)')

    # SECTION 4: HIGH-LEVEL EDGE COMPUTING & AI (Raspberry Pi 4 / 5)
    draw_box(4, 65, 92, 26, "LAYER 3: EDGE ROBOTICS COMPUTE & COMPUTER VISION (Raspberry Pi / Host PC)", "", '#111827', '#1E293B', '#A855F7')
    draw_box(6, 68, 18, 19, "Threaded Camera\nStream", "Lock-free Capture\nZero Buffer Latency\nSynthetic Field Gen", '#1E293B', '#8B5CF6')
    draw_box(26, 68, 20, 19, "Monocular CV\nObstacle Avoidance", "Ground ROI Isolator\nCanny Edge / Otsu\n3-Zone Density Map\n(Left / Center / Right)", '#1E293B', '#06B6D4')
    draw_box(48, 68, 20, 19, "YOLOv8 Edge\nInference", "Deep Learning Engine\nLeaf Disease BBox\nPixel Target Offset\nHeuristic CV Fallback", '#1E293B', '#EC4899')
    draw_box(70, 68, 24, 19, "Mission Controller &\nNavigation Brain", "Finite State Machine\nActive Leaf Aiming\nEmergency Braking\nDiagnostic HUD Display", '#1E293B', '#10B981')

    # Internal Connections in Layer 3
    draw_solid_arrow(85, 18, 85, 68, '#8B5CF6', 'USB Video Feed')
    draw_solid_arrow(24, 77, 26, 77, '#06B6D4', 'Frames')
    draw_solid_arrow(24, 73, 48, 73, '#EC4899', 'Frames')
    draw_solid_arrow(46, 77, 70, 77, '#06B6D4', 'Zone Density')
    draw_solid_arrow(68, 73, 70, 73, '#EC4899', 'Disease Targets')
    draw_solid_arrow(78, 68, 45, 60, '#38BDF8', 'Actuation Commands')

    plt.tight_layout()
    plt.savefig('assets/system_architecture.png', facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print("Generated assets/system_architecture.png successfully.")

def generate_workflow_pipeline():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    fig.patch.set_facecolor('#0B0F19')
    ax.set_facecolor('#0B0F19')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Title
    ax.text(50, 96, "AGRICULTURE ROVER - AUTONOMOUS MISSION WORKFLOW PIPELINE", 
            color='#00FFCC', fontsize=17, fontweight='bold', ha='center', fontfamily='sans-serif')
    ax.text(50, 93, "Perception -> 3-Zone Spatial Avoidance -> 0-180° Panoramic Scan -> Targeted Spraying Cycle", 
            color='#94A3B8', fontsize=10, ha='center', fontfamily='sans-serif')

    def draw_node(x, y, w, h, title, desc, border_color, fill_color='#1E293B'):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.0",
                                     facecolor=fill_color, edgecolor=border_color, linewidth=2.2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 2.8, title, color='#FFFFFF', fontsize=9.5, fontweight='bold', ha='center')
        ax.text(x + w/2, y + h/2 - 0.8, desc, color='#CBD5E1', fontsize=8, ha='center', va='center')

    def draw_arrow(x1, y1, x2, y2, color='#38BDF8', label=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2, mutation_scale=15))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 1.2, label, color='#F8FAFC', fontsize=7.5, fontweight='bold', ha='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='#0F172A', edgecolor=color, lw=1))

    # ROW 1: Acquisition & Perception
    draw_node(5, 74, 18, 14, "1. Camera Capture", "Threaded Stream\n640x480 @ 30 FPS\nZero Frame Lag", '#3B82F6')
    draw_arrow(23, 81, 29, 81, '#3B82F6', 'Raw Frame')

    draw_node(29, 74, 20, 14, "2. Ground ROI Isolator", "Crop Top Horizon\nFocus on Bottom 55%\nPath Surface Extraction", '#06B6D4')
    draw_arrow(49, 81, 55, 81, '#06B6D4', 'Ground ROI')

    draw_node(55, 74, 20, 14, "3. Obstacle Segmenter", "Canny Edge & Otsu Thresh\nMorphological Dilation\nContour Integration", '#10B981')
    draw_arrow(75, 81, 81, 81, '#10B981', 'Binary Mask')

    draw_node(81, 74, 15, 14, "4. 3-Zone Density", "Left / Center / Right\nOccupancy Densities\nSteer Decision Matrix", '#F59E0B')

    # ROW 2: Decision & Navigation
    draw_arrow(88, 74, 88, 56, '#F59E0B', 'Spatial Metrics')
    draw_node(74, 42, 22, 14, "5. Navigation Brain", "Ultrasonic Check (<25cm)\nState: CRUISING /\nAVOID_L / AVOID_R", '#10B981')

    draw_arrow(74, 49, 58, 49, '#10B981', 'Field Path Clear')
    draw_node(40, 42, 18, 14, "6. Forward Drive", "Skid-Steer Differential\nCruise Speed PWM\nRocker-Bogie Traction", '#3B82F6')

    # ROW 3: Parallel Panoramic Scan & YOLO
    draw_node(5, 42, 22, 14, "7. Pan 0°-180° Sweep", "Non-blocking Servo Sweep\nPanoramic Surrounds\nDynamic Step Scanning", '#8B5CF6')
    draw_arrow(16, 74, 16, 56, '#8B5CF6', 'Active Frame')
    draw_arrow(27, 49, 40, 49, '#8B5CF6')

    draw_node(5, 12, 24, 16, "8. YOLOv8 Disease AI", "Inference on Leaves\nDetect: Blight, Rust,\nLeaf Spot, Powdery Mildew\nCalculate Pixel Center", '#EC4899')
    draw_arrow(16, 42, 16, 28, '#EC4899', 'Crop View')

    # ROW 4: Targeted Action
    draw_node(40, 12, 24, 16, "9. Precision Aiming", "1. Emergency Rover Pause\n2. Pan Sweep Halts\n3. FOV Offset Math\n4. Aim Nozzle directly at Leaf", '#F59E0B')
    draw_arrow(29, 20, 40, 20, '#EC4899', 'Infected Leaf Spotted')

    draw_node(74, 12, 22, 16, "10. Fertilizer Spray", "Optocoupler Relay ON\n12V Diaphragm Pump Pulse\nAccurate Chemical Dosing\nCooldown Enforced", '#EF4444')
    draw_arrow(64, 20, 74, 20, '#F59E0B', 'Target Locked')

    # Loop back
    draw_arrow(85, 28, 85, 42, '#10B981', 'Spray Complete -> Resume Cruising')

    plt.tight_layout()
    plt.savefig('assets/workflow_pipeline.png', facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print("Generated assets/workflow_pipeline.png successfully.")

if __name__ == "__main__":
    generate_system_architecture()
    generate_workflow_pipeline()
