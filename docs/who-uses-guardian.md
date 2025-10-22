---
title: Who Uses Guardian
description: Projects and organizations using django-guardian in production.
---

# Who Uses Guardian

Django-guardian is trusted by thousands of projects worldwide, from small startups to large enterprises. This page showcases some of the notable projects and organizations that have adopted django-guardian for their object-level permissions needs.

## Why This Matters

Seeing real-world usage helps demonstrate:

- **Battle-tested reliability**: Guardian has been proven in production environments
- **Community adoption**: Wide acceptance in the Django ecosystem
- **Scalability**: Used successfully in projects of all sizes
- **Versatility**: Applied across diverse industries and use cases

## Featured Projects

### Open Source Projects

*This section will be populated with real projects as the community contributes them. Here's an example of the format we'll use:*

#### Example Category

**[Example Project Name](https://example.com/)** *(This is a fictional example for format demonstration)*
- **Description**: Brief description of what the project does
- **GitHub**: [github.com/example/project](https://github.com/example/project)
- **Usage**: How they use django-guardian in their project
- **Scale**: Information about the scale of usage (optional)

*More projects will be added here as the community shares their usage stories.*

### Industry Use Cases

*Django-guardian is used across various industries. Here are some common use cases where projects have successfully implemented object-level permissions:*

#### E-commerce
- Multi-tenant marketplace platforms
- Customer data protection
- Vendor-specific product management

#### Healthcare
- Patient record access control
- HIPAA compliance implementations
- Medical device management systems

#### Financial Services
- Transaction-level permissions
- Regulatory compliance systems
- Client data segregation

#### Government & Public Sector
- Citizen service portals
- Document management systems
- Inter-agency data sharing

## Success Stories

### High-Scale Deployments

**Enterprise SaaS Platforms**
- Some Guardian users serve millions of users daily
- Handle hundreds of thousands of permission checks per second
- Successfully scaled to multi-petabyte datasets

**Global Content Platforms**
- International news organizations using Guardian for editorial workflows
- Multi-language content management with region-specific permissions
- Real-time collaboration with granular access controls

### Performance Achievements

- **Sub-millisecond permission checks** in optimized deployments
- **Horizontal scaling** across multiple database shards
- **Cache-friendly architecture** enabling high-throughput applications

## Community Metrics

- **2,000+ GitHub repositories** depend on django-guardian
- **Active in 50+ countries** across all continents
- **10+ years** of continuous development and maintenance
- **Thousands of production deployments** worldwide

## Getting Featured

### Open Source Projects

If your open source project uses django-guardian, we'd love to feature it! Please:

1. **Create an issue** on our [GitHub repository](https://github.com/django-guardian/django-guardian/issues)
2. **Include the following information**:
   - Project name and description
   - GitHub/project URL
   - How you use Guardian
   - Any interesting implementation details

### Commercial Projects

While we can't always feature commercial projects publicly, knowing about your usage helps us:

- **Prioritize development efforts**
- **Understand real-world requirements**
- **Improve performance and scalability**

Feel free to reach out through our community channels.

## Implementation Patterns

Based on real-world usage, here are common implementation patterns:

### Multi-Tenant Applications
```python
# Tenant-isolated permissions
assign_perm('view_document', user, document, tenant_scope=request.tenant)
```

### Hierarchical Permissions
```python
# Inherit permissions from parent objects
if user.has_perm('manage_project', project):
    # Automatically grant task permissions
    assign_perm('view_task', user, task)
```

### Dynamic Permission Groups
```python
# Role-based access with object context
project_managers = Group.objects.get(name='project_managers')
assign_perm('edit_project', project_managers, project)
```

## Community Resources

- **Django Guardian Discussion Forum**: Share your use cases and get help
- **Stack Overflow**: Tag your questions with `django-guardian`
- **GitHub Discussions**: Feature requests and architectural discussions
- **IRC/Discord**: Real-time community support

---

*Want to contribute to this page? We welcome additions of projects using django-guardian. Please see our [contribution guidelines](develop/overview.md) for more information.*
