from google.antigravity import LocalAgentConfig, CapabilitiesConfig

# FDE-TechLead-PM: 技術戦略マネージャー
TECHLEAD_CONFIG = LocalAgentConfig(
    system_instructions=(
        "You are FDE-TechLead-PM, the lead architect for Touchless-FDE."
        "Your task is to design GCP and Firebase infrastructure architectures "
        "based on the PRD provided by FDE-Consultant-PM, and prepare execution steps for Jules."
    ),
    capabilities=CapabilitiesConfig() # Read-only defaults
)
