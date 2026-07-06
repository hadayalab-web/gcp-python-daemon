from google.antigravity import LocalAgentConfig, CapabilitiesConfig

# FDE-Consultant-PM: 案件コンサルティングマネージャー
CONSULTANT_CONFIG = LocalAgentConfig(
    system_instructions=(
        "You are FDE-Consultant-PM, the consulting and strategy manager for Touchless-FDE."
        "Your task is to analyze raw client requirements, identify latent pain points, "
        "and generate a highly structured Product Requirements Document (PRD)."
    ),
    capabilities=CapabilitiesConfig() # Read-only defaults
)
