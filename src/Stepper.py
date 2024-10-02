import streamlit as st
import streamlit.components.v1 as components


class Stepper:

    def __init__(self, steps, labels, fill_color="#30ACC3", height=100):
        self.total_steps = steps
        self.labels = labels
        self.height = height
        self.fill_color = fill_color
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 0

    def create_stepper_html(self):
        html_code = f"""
        <style>
            .stepper-container {{
                width: 100%;
                margin: 0 auto;
            }}
            .stepper-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
                margin-right: 24px;
                margin-left: 24px;
                margin-bottom: 20px;
            }}
            .step {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: #e0e0e0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                position: relative;
                z-index: 2;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}
            .step.active {{
                background-color: {self.fill_color};
                color: white;
            }}
            .step:hover {{
                background-color: {self.fill_color};
                color: white;
            }}
            .step-label {{
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                margin-top: 0.5 rem;
                text-align: center;
                word-wrap: break-word;
                font-size: 0.875 rem;
                color: #333;
                width: auto;
            }}
            .progress-line {{
                position: absolute;
                top: 15px;
                left: 0;
                width: 100%;
                height: 2px;
                background-color: #e0e0e0;
                z-index: 1;
            }}
            .progress-line-fill {{
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                background-color: {self.fill_color};
                transition: width 0.3s ease;
            }}
        </style>
        <div class="stepper-container">
            <div class="stepper-bar" id="stepper-bar">
                <div class="progress-line">
                    <div class="progress-line-fill" id="progress-fill"></div>
                </div>
        """

        for i in range(self.total_steps):
            class_name = "step active" if i <= st.session_state.current_step else "step"
            # html_code += f"""
            #     <div class="{class_name}" onclick="updateStep({i})">
            #         {i + 1}
            #         <div class="step-label">{self.labels[i]}</div>
            #     </div>
            # """
            html_code += f"""
                            <div class="{class_name}">
                                {i + 1}
                                <div class="step-label">{self.labels[i]}</div>
                            </div>
                        """

        html_code += """
            </div>
        </div>
        <script>
            let currentStep = """ + str(st.session_state.current_step) + """;
            const totalSteps = """ + str(self.total_steps) + """;
    
            function updateStep(step) {
                currentStep = step;
                updateStepperBar();
                updateProgressLine();
                window.parent.postMessage({type: 'step_update', step: step}, '*');
            }
    
            function updateStepperBar() {
                const steps = document.querySelectorAll('.step');
                steps.forEach((step, index) => {
                    if (index <= currentStep) {
                        step.classList.add('active');
                    } else {
                        step.classList.remove('active');
                    }
                });
            }
    
            function updateProgressLine() {
                const progressFill = document.getElementById('progress-fill');
                const progress = currentStep / (totalSteps - 1) * 100;
                progressFill.style.width = `${progress}%`;
            }
    
            updateProgressLine();
        </script>
        """

        return html_code

    def render(self):
        components.html(self.create_stepper_html(), height=self.height + 100)

    def get_current_step(self):
        return st.session_state.current_step

    def set_current_step(self, step):
        if 0 <= step < self.total_steps:
            st.session_state.current_step = step
            st.rerun()
