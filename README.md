# Collaborative AI Layer (CAL)

## Overview
The Collaborative AI Layer (CAL) is an intelligent orchestration platform designed to manage and streamline tasks across a team of specialized AI agents. Each agent is tailored to handle specific domains, such as customer communication, document retrieval, technical content creation, and market research. The system's core component, the Agent Orchestrator, dynamically routes requests to the appropriate agents based on the task's requirements, aggregates responses, and presents unified, actionable outputs to users.

CAL features a web interface for user interaction and a RESTful API for programmatic access, ensuring seamless interaction, adaptability, and efficiency. It is ideal for environments requiring cross-functional collaboration and intelligent task management.

## Key Features
- **Dynamic Task Routing:** Intelligently routes tasks to the most suitable specialized agents.
- **Collaborative Workflows:** Orchestrates multiple agents to work together on complex tasks.
- **Response Aggregation:** Aggregates responses from multiple agents into a unified, coherent output.
- **Web Interface:** A user-friendly web interface for interacting with the system, viewing results, and managing workflows.
- **RESTful API:** A comprehensive set of API endpoints for programmatic interaction with the platform.
- **Feedback Management:** A system for incorporating user feedback to improve agent performance.
- **Quality Assurance:** Automated quality checks and fact verification for agent responses.
- **Firestore Integration:** Uses Google Firestore for scalable and reliable data storage.

## Getting Started

### Prerequisites
- Python 3.11+
- Poetry for dependency management
- Access to a Google Cloud project with Firestore enabled

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rnolden2/cal_agent.git
    cd cal_agent
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

3.  **Set up environment variables:**
    You will need to set up authentication for Google Cloud. Please refer to the [Google Cloud documentation](https://cloud.google.com/docs/authentication/getting-started) for details on how to set up your credentials.

### Running the Application
To run the application locally, use the following command:
```bash
poetry run uvicorn app.main:app --reload
```
The application will be available at `http://127.0.0.1:8000`.

## Web Interface
The web interface provides a user-friendly way to interact with the CAL platform. It includes the following pages:
-   **Home:** The main landing page for submitting tasks.
-   **Market Research:** A dedicated interface for market research tasks.
-   **Workflow Dashboard:** A dashboard for monitoring the status of ongoing workflows.
-   **Report Interface:** An interface for generating and viewing reports.
-   **Feedback Display:** A page for viewing and managing feedback.
-   **History:** A history of all past requests and responses.

## API Endpoints
The following are the main API endpoints provided by the application:

-   `POST /agent`: The primary endpoint for all agent interactions. It accepts a JSON payload with the task details and returns the orchestrated response.
-   `GET /responses`: Fetches recent agent responses, with optional filtering by `topic_id` and `user_id`.
-   `GET /responses/topic/{topic_id}`: Retrieves all agent responses for a specific topic.
-   `GET /topic/{topic_id}/summary`: Provides a summary of a topic, including the agents involved and the response count.
-   `GET /responses/search`: Searches for agent responses by tags and keywords.

## Agents

| **Agent Name**         | **Description**                                                                                   |
|-------------------------|---------------------------------------------------------------------------------------------------|
| **CustomerConnect**     | Assists in drafting professional email communications.                                           |
| **DocumentMaster**      | Retrieves and organizes documents such as technical papers, presentations, and standards.         |
| **Editor**              | Edits all written documentation using a custom format and writing style.                          |
| **Engineer**            | Provides insights into technical terms, equations, and best practices.                            |
| **ProfessionalMentor**  | Provides personalized coaching for improving work performance and task prioritization.            |
| **RivalWatcher**        | Gathers and updates information on competitors for strategic decision-making.                     |
| **Sales**               | Provides recommendations to optimize sales and maximize business opportunities.                     |
| **TechnicalWizard**     | Produces high-quality technical content, such as proposal sections and technical bullet points.   |
| **TrendTracker**        | Monitors market trends, solicitations, and programs related to specific industries.               |
| **General**             | A general-purpose agent for tasks that do not fall into a specific domain.                        |

## How to Contribute
We welcome contributions to the Collaborative AI Layer project. Please feel free to open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
