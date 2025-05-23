# Ticketing System Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [Database Structure](#database-structure)
5. [Ticket Lifecycle](#ticket-lifecycle)
6. [Service Hierarchy](#service-hierarchy)
7. [Key Features](#key-features)
8. [Security Features](#security-features)
9. [Workflow Processes](#workflow-processes)
10. [Entity Relationship Diagram](#entity-relationship-diagram)

## Introduction

The Ticketing System is a comprehensive web-based application designed to manage and track support tickets across multiple companies. It follows a multi-tenant architecture where each company has its own set of users, tickets, and service categories. The system provides a structured approach to handling customer support requests, internal IT issues, and service management.

This documentation is intended for developers who need to understand the system's architecture, data models, and workflows. It provides a high-level overview of the system's components and how they interact with each other.

## System Architecture

The Ticketing System is built using the Django web framework, following the Model-View-Template (MVT) architectural pattern. The system consists of the following main components:

### Core Applications

1. **Accounts**: Manages user authentication, profiles, and company information
2. **User Tickets**: Handles ticket creation, management, and the service hierarchy

### Key Technologies

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: Relational database (compatible with PostgreSQL, MySQL, SQLite)
- **Authentication**: Django's built-in authentication system with custom extensions
- **File Storage**: Django's file storage system for attachments

### Directory Structure

The application follows Django's recommended project structure:

- **ticketing_system/**: Main project directory
  - **accounts/**: User and company management
  - **user_tickets/**: Ticket and service management
  - **templates/**: HTML templates
  - **static/**: Static files (CSS, JavaScript, images)
  - **media/**: User-uploaded files

## User Roles and Permissions

The system implements a hierarchical role-based access control system with the following user roles:

### 1. Superadmin (System Administrator)

- Has complete access to all features and data
- Can manage all companies, users, and tickets
- Can configure system-wide settings
- Can access the Django admin interface

### 2. Company Agent

- Can manage tickets from companies they are assigned to
- Can view and respond to tickets from multiple companies
- Cannot access system configuration settings
- Typically used by support staff who handle tickets from multiple clients

### 3. Company Staff

- Can manage tickets within their own company
- Can create and edit tickets
- Can manage users within their company (if they have the appropriate permissions)
- Cannot access data from other companies

### 4. Regular User

- Can create and view their own tickets
- Can view tickets from their company
- Limited access to administrative features

### Permission System

The system uses Django's permission system with custom extensions:

- **can_manage_users**: Allows user management
- **can_manage_tickets**: Allows ticket management
- **can_manage_company**: Allows company settings management
- **can_view_assigned_companies**: Allows viewing tickets from assigned companies
- **can_manage_assigned_tickets**: Allows managing tickets from assigned companies

## Database Structure

The system uses a relational database with the following main entities:

### User Management

1. **User**: Extended Django user model with company association
   - Core user information (username, password, email)
   - Company association
   - Staff and superuser flags
   - Custom permissions

2. **Profile**: Extended user profile information
   - Personal details (job title, location, phone)
   - Preferences (language, timezone)
   - MFA (Multi-Factor Authentication) settings
   - Profile picture

3. **Company**: Organization entity
   - Company details (name, address, phone)
   - Active status
   - Unique slug for URL identification

4. **StaffCompanyAssignment**: Links staff users to companies they can manage
   - User reference
   - Company reference
   - Assignment metadata (who assigned, when)

### Ticket Management

1. **Ticket**: Core ticket entity
   - Basic information (title, description)
   - Status (Open, In Progress, Resolved, Closed)
   - Priority (Low, Medium, High, Critical)
   - Impact (Person, Department, Service)
   - Associations (company, category, created by, assigned to)
   - Timestamps (created, updated, resolved)

2. **TicketAttachment**: Files attached to tickets
   - File reference
   - Metadata (filename, type, size)
   - Upload information (who uploaded, when)

3. **TicketComment**: Comments on tickets
   - Comment text
   - Author information
   - Timestamps

### Service Hierarchy

1. **ServiceFamily**: Top-level service category
   - Name and description
   - Company association

2. **ServiceType**: Mid-level service category
   - Name and description
   - Parent ServiceFamily

3. **ServiceCategory**: Detailed service category
   - Name and description
   - Parent ServiceType

## Ticket Lifecycle

Tickets in the system follow a defined lifecycle:

### 1. Creation

- User selects a service category
- User fills in ticket details (title, description, priority, impact)
- User can attach files and tag other users
- System assigns the ticket to the appropriate staff member
- System sends notifications to relevant parties

### 2. Processing

- Assigned staff reviews the ticket
- Staff can update status, priority, or assignment
- Staff and users can add comments
- Staff can request additional information
- All changes are tracked and notifications sent

### 3. Resolution

- Staff resolves the issue
- Resolution details are documented
- Ticket status is changed to "Resolved"
- System records resolution time
- Notifications are sent to the ticket creator

### 4. Closure

- After verification, the ticket can be closed
- Closed tickets are archived but remain accessible
- Reporting and analytics can be performed on closed tickets

### Status Transitions

- **Open**: Initial state when a ticket is created
- **In Progress**: Work has begun on the ticket
- **Resolved**: The issue has been fixed but awaiting verification
- **Closed**: The ticket has been completed and verified

## Service Hierarchy

The system organizes services in a three-level hierarchy:

### 1. Service Family

- Top-level categorization
- Examples: IT Support, HR Services, Facilities Management
- Each company can define its own service families

### 2. Service Type

- Mid-level categorization within a family
- Examples: Hardware Support, Software Support, Network Issues
- Helps in routing tickets to the right department

### 3. Service Category

- Detailed categorization within a type
- Examples: Printer Issues, Software Installation, Password Reset
- Allows for precise tracking and reporting

This hierarchical approach enables:
- Organized ticket categorization
- Accurate routing of tickets
- Detailed reporting and analytics
- Structured knowledge base organization

## Key Features

### Ticket Management

- Create, view, edit, and close tickets
- Attach files to tickets
- Add comments and updates
- Track ticket status and history
- Search and filter tickets
- Export ticket data to CSV

### User Management

- User registration and authentication
- Profile management
- Role-based access control
- Multi-factor authentication
- Password reset functionality

### Company Management

- Multi-tenant architecture
- Company-specific service categories
- Company-specific user management
- Staff assignment to companies

### Notification System

- Email notifications for ticket events
- Customizable notification preferences
- In-app notifications

### Reporting and Analytics

- Ticket volume by category
- Resolution time metrics
- Staff performance metrics
- Company-specific reporting

## Security Features

The system implements several security features:

### Authentication Security

- Secure password storage using Django's password hashing
- Multi-factor authentication option
- Password complexity requirements
- Account lockout after failed attempts
- Secure password reset process

### Authorization Controls

- Role-based access control
- Company data isolation
- Object-level permissions
- Session management and timeout

### Data Protection

- Input validation and sanitization
- Protection against common web vulnerabilities
- Secure file upload handling
- Data encryption for sensitive information

## Workflow Processes

### Ticket Creation Process

1. User navigates to "Create New Ticket"
2. User selects the appropriate service category
3. User fills in ticket details
4. User submits the ticket
5. System assigns the ticket based on category and company
6. System sends notifications to relevant parties

### Ticket Assignment Process

1. New tickets are initially unassigned or assigned to a default handler
2. Staff can manually assign tickets
3. Automatic assignment can be configured based on:
   - Service category
   - Company
   - Workload balancing
   - Skill matching

### Ticket Resolution Process

1. Staff investigates the issue
2. Staff updates the ticket with findings
3. Staff implements the solution
4. Staff documents the resolution
5. Staff changes status to "Resolved"
6. User verifies the resolution
7. Ticket is closed or reopened if necessary

## Entity Relationship Diagram

Below is a simplified entity relationship diagram showing the main entities and their relationships:

```
User (1) --- (1) Profile
User (N) --- (1) Company
User (1) --- (N) Ticket (created_by)
User (1) --- (N) Ticket (assigned_to)
User (N) --- (N) Ticket (contacts)

Company (1) --- (N) ServiceFamily
Company (1) --- (N) Ticket

ServiceFamily (1) --- (N) ServiceType
ServiceType (1) --- (N) ServiceCategory
ServiceCategory (1) --- (N) Ticket

Ticket (1) --- (N) TicketAttachment
Ticket (1) --- (N) TicketComment

User (1) --- (N) TicketAttachment (uploaded_by)
User (1) --- (N) TicketComment (created_by)

User (N) --- (N) Company (through StaffCompanyAssignment)
```

This diagram illustrates the relationships between the main entities in the system, showing how users, companies, tickets, and services are interconnected.

---

This documentation provides a comprehensive overview of the Ticketing System. For more detailed information on specific components or processes, please refer to the code comments and inline documentation.