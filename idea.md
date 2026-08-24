# Problem
AI video generation is hidden behind paywall that get increasily expensier on token consumption, and video creation without AI feels an slow and outdated process, and even tho open source video generation models are freely accesible, its usage is restricted by the lack of easy implementation and most importantly lack of resources.

# Solution
Open source platform that auto detects hardware capacity and utilizes the best model available for generating video. Offering an intuitive platform for generating the video, and also providing SDK integration for inclusing video generation into your workflows. Besides it provides and MCP server for accessing the API to integrate into your AI workflows.

# Products
- API: Contains auto-model selection engine and capabilities for video generation based on characteristics framework.
- SDK: Programatic access to API to integrate AI video generation into workflows.
- MCP: Agentic access to API to integrate AI video generation into agentic workflows.

# Components

1. API
    1. Video generation engine
        1. Characteristics research
        2. Prompt structure
        3. Feedback loop
        4. Generation
        5. Storage/Buffer
    
    2. Model detection engine
        1. Model syncronization
            1. Model Schema
                1. Hardware requirements
                2. Software characteristics
            2. Information pulling / local definition with api versioning
        2. Hardware characteristics detection
        3. Model matching
    
    3. Authentication / Authorization

    4. Sensible data security

    4. Cloud Integration

2. SDK
    1. Versioning matching API
    2. Authentication / Authorization
    3. Language support

3. MCP
    1. Generalized context
    2. Endpoint customization
        1. Extensible context for API
