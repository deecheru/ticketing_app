# Ticketing System Architecture

```mermaid
graph TD
    subgraph Frontend
        UI[User Interface]
        Templates[HTML Templates]
        Static[Static Files]
    end

    subgraph Backend
        Django[Django Framework]
        Auth[Authentication]
        Views[Views/Controllers]
        Models[Data Models]
    end

    subgraph Database
        DB[(Database)]
        Files[File Storage]
    end

    subgraph External
        Email[Email Service]
        Notifications[Notification System]
    end

    %% Frontend connections
    UI --> Templates
    UI --> Static
    UI --> Django

    %% Backend connections
    Django --> Auth
    Django --> Views
    Views --> Models
    Models --> DB
    Models --> Files

    %% External connections
    Django --> Email
    Django --> Notifications

    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b
    classDef backend fill:#e8f5e9,stroke:#1b5e20
    classDef database fill:#fff3e0,stroke:#e65100
    classDef external fill:#fce4ec,stroke:#880e4f

    class UI,Templates,Static frontend
    class Django,Auth,Views,Models backend
    class DB,Files database
    class Email,Notifications external
```

## Component Description

### Frontend Layer
- **User Interface**: Web interface for users
- **HTML Templates**: Reusable page layouts
- **Static Files**: CSS, JavaScript, and images

### Backend Layer
- **Django Framework**: Core application framework
- **Authentication**: User authentication and authorization
- **Views/Controllers**: Business logic and request handling
- **Data Models**: Database schema and relationships

### Database Layer
- **Database**: Stores application data
- **File Storage**: Manages uploaded files and attachments

### External Services
- **Email Service**: Handles email notifications
- **Notification System**: Manages system notifications 