"""Template management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
import re
from jinja2 import Template as Jinja2Template, UndefinedError

from src.api.models import APIResponse
from src.api.security.auth import get_current_user
from src.api.schemas.management import (
    TemplatesListResponse,
    TemplateInfo,
    TemplateDetailResponse,
    CreateTemplateRequest,
    CreatedTemplateResponse,
    UpdateTemplateRequest,
    UpdatedTemplateResponse,
    DeletedTemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from src.templates.manager import TemplateManager
from src.templates.loader import Template
from src.logging.logger import StructuredLogger

router = APIRouter(tags=["templates"])
logger = StructuredLogger(__name__)

# Global template manager instance
template_manager = TemplateManager()

# Track custom templates in-memory (name -> template info)
_custom_templates: Dict[str, Dict[str, Any]] = {}


def _extract_variables(content: str) -> List[str]:
    """Extract Jinja2 variables from template content."""
    # Find all {{ variable_name }} patterns
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    matches = re.findall(pattern, content)
    return sorted(list(set(matches)))


def _is_custom_template(name: str) -> bool:
    """Check if a template is custom (user-created)."""
    return name in _custom_templates


@router.get(
    "/templates",
    response_model=APIResponse,
    summary="List All Templates",
    tags=["Templates"],
)
async def list_templates(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List all available templates.

    Returns all templates (built-in and custom) with basic information.
    """
    try:
        templates_data = []
        seen_names = set()

        # Get built-in and custom templates from manager
        all_templates = template_manager.list_templates()
        for template in all_templates:
            template_data = TemplateInfo(
                name=template.name,
                action=template.action,
                description=template.description,
                variables=_extract_variables(template.user_prompt_template),
            )
            templates_data.append(template_data)
            seen_names.add(template.name)

        # Add templates from manager's custom_templates cache
        for (action, name), template in template_manager.custom_templates.items():
            if name not in seen_names:
                template_data = TemplateInfo(
                    name=name,
                    action=action,
                    description=template.description,
                    variables=_extract_variables(template.user_prompt_template),
                )
                templates_data.append(template_data)
                seen_names.add(name)

        # Add in-memory custom templates
        for name, custom_info in _custom_templates.items():
            if name not in seen_names:
                template_data = TemplateInfo(
                    name=name,
                    action=custom_info["action"],
                    description=custom_info.get("description", ""),
                    variables=custom_info.get("variables", []),
                )
                templates_data.append(template_data)
                seen_names.add(name)

        response_data = TemplatesListResponse(templates=templates_data)

        logger.info(
            "Templates listed",
            extra={
                "user_id": current_user.get("user_id"),
                "template_count": len(templates_data),
            },
        )

        return APIResponse(success=True, data=response_data)
    except Exception as e:
        logger.error(
            "Error listing templates",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.get(
    "/templates/{id}",
    response_model=APIResponse,
    summary="Get Template Details",
    tags=["Templates"],
)
async def get_template_detail(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get detailed information about a specific template.

    Returns the template content, variables, and metadata.
    """
    try:
        # Check in-memory custom templates first
        if id in _custom_templates:
            custom_info = _custom_templates[id]
            response_data = TemplateDetailResponse(
                name=id,
                action=custom_info["action"],
                content=custom_info["content"],
                variables=custom_info.get("variables", []),
            )

            logger.info(
                "Custom template detail retrieved",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": id,
                },
            )

            return APIResponse(success=True, data=response_data)

        # Check template manager's custom_templates cache (used by tests)
        for (action, name), template in template_manager.custom_templates.items():
            if template.name == id:
                response_data = TemplateDetailResponse(
                    name=id,
                    action=template.action,
                    content=template.user_prompt_template,
                    variables=_extract_variables(template.user_prompt_template),
                )

                logger.info(
                    "Template detail retrieved from manager cache",
                    extra={
                        "user_id": current_user.get("user_id"),
                        "template_name": id,
                    },
                )

                return APIResponse(success=True, data=response_data)

        # Try to find template by searching all available templates
        all_templates = template_manager.list_templates()
        for template in all_templates:
            if template.name == id:
                response_data = TemplateDetailResponse(
                    name=id,
                    action=template.action,
                    content=template.user_prompt_template,
                    variables=_extract_variables(template.user_prompt_template),
                )

                logger.info(
                    "Template detail retrieved",
                    extra={
                        "user_id": current_user.get("user_id"),
                        "template_name": id,
                    },
                )

                return APIResponse(success=True, data=response_data)

        logger.warning(
            "Attempted to get non-existent template",
            extra={
                "user_id": current_user.get("user_id"),
                "template_name": id,
            },
        )
        raise HTTPException(status_code=404, detail=f"Template not found: {id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving template detail",
            extra={"error": str(e), "template_name": id},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve template details")


@router.post(
    "/templates/use",
    response_model=APIResponse,
    summary="Use/Apply Template",
    tags=["Templates"],
)
async def use_template(
    template_id: str,
    action: str,
    variables: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Use/apply a template to generate a prompt.

    Renders the template with the provided variables and returns the generated prompt.
    """
    try:
        # Get template content
        content = None

        if template_id in _custom_templates:
            content = _custom_templates[template_id]["content"]
        else:
            # Check manager's custom_templates cache
            for (action, name), template in template_manager.custom_templates.items():
                if template.name == template_id:
                    content = template.user_prompt_template
                    break

            if content is None:
                all_templates = template_manager.list_templates()
                for template in all_templates:
                    if template.name == template_id:
                        content = template.user_prompt_template
                        break

        if content is None:
            logger.warning(
                "Attempted to use non-existent template",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_id": template_id,
                },
            )
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        # Render template using Jinja2
        try:
            jinja_template = Jinja2Template(content)
            generated_prompt = jinja_template.render(**variables)
        except UndefinedError as e:
            logger.warning(
                "Template rendering failed - undefined variable",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_id": template_id,
                    "error": str(e),
                },
            )
            raise HTTPException(
                status_code=400,
                detail=f"Missing required variable: {str(e)}",
            )

        response_data = {
            "generated_prompt": generated_prompt,
            "success": True,
        }

        logger.info(
            "Template used to generate prompt",
            extra={
                "user_id": current_user.get("user_id"),
                "template_id": template_id,
                "action": action,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error using template",
            extra={"error": str(e), "template_id": template_id},
        )
        raise HTTPException(status_code=500, detail="Failed to use template")


@router.post(
    "/templates",
    response_model=APIResponse,
    summary="Create Custom Template",
    tags=["Templates"],
)
async def create_template(
    request: CreateTemplateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create a new custom template.

    Creates a user-defined template that can be used for code generation.
    """
    try:
        # Check if template already exists
        if request.name in _custom_templates:
            logger.warning(
                "Attempted to create duplicate template",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": request.name,
                },
            )
            raise HTTPException(
                status_code=409,
                detail=f"Template already exists: {request.name}",
            )

        # Check builtin templates
        builtin = template_manager.list_templates()
        if any(t.name == request.name for t in builtin):
            logger.warning(
                "Attempted to create template with builtin name",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": request.name,
                },
            )
            raise HTTPException(
                status_code=409,
                detail=f"Template name already exists (built-in): {request.name}",
            )

        # Extract variables from content
        variables = _extract_variables(request.content)

        # Store custom template
        _custom_templates[request.name] = {
            "action": request.action,
            "content": request.content,
            "description": request.description,
            "variables": variables,
            "custom": True,
        }

        response_data = CreatedTemplateResponse(
            name=request.name,
            created=True,
        )

        logger.info(
            "Custom template created",
            extra={
                "user_id": current_user.get("user_id"),
                "template_name": request.name,
                "action": request.action,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating template",
            extra={"error": str(e), "template_name": request.name},
        )
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.put(
    "/templates/{id}",
    response_model=APIResponse,
    summary="Update Template",
    tags=["Templates"],
)
async def update_template(
    id: str,
    request: UpdateTemplateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update an existing template.

    Updates the template content and/or description.
    """
    try:
        if id not in _custom_templates:
            logger.warning(
                "Attempted to update non-existent template",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": id,
                },
            )
            raise HTTPException(status_code=404, detail=f"Template not found: {id}")

        # Extract variables from new content
        variables = _extract_variables(request.content)

        # Update custom template
        _custom_templates[id]["content"] = request.content
        _custom_templates[id]["description"] = request.description
        _custom_templates[id]["variables"] = variables

        response_data = UpdatedTemplateResponse(
            name=id,
            updated=True,
        )

        logger.info(
            "Custom template updated",
            extra={
                "user_id": current_user.get("user_id"),
                "template_name": id,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating template",
            extra={"error": str(e), "template_name": id},
        )
        raise HTTPException(status_code=500, detail="Failed to update template")


@router.delete(
    "/templates/{id}",
    response_model=APIResponse,
    summary="Delete Template",
    tags=["Templates"],
)
async def delete_template(
    id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a custom template.

    Only custom templates can be deleted. Built-in templates cannot be removed.
    """
    try:
        # Check if template is custom
        if id not in _custom_templates:
            logger.warning(
                "Attempted to delete non-custom template",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": id,
                },
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot delete built-in templates",
            )

        # Delete custom template
        del _custom_templates[id]

        response_data = DeletedTemplateResponse(
            name=id,
            deleted=True,
        )

        logger.info(
            "Custom template deleted",
            extra={
                "user_id": current_user.get("user_id"),
                "template_name": id,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting template",
            extra={"error": str(e), "template_name": id},
        )
        raise HTTPException(status_code=500, detail="Failed to delete template")


@router.post(
    "/templates/{id}/preview",
    response_model=APIResponse,
    summary="Preview Template Rendering",
    tags=["Templates"],
)
async def preview_template(
    id: str,
    request: TemplatePreviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Preview a template with the provided variables.

    Renders the template with the given variables to show what the output will look like.
    """
    try:
        # Get template content
        content = None

        if id in _custom_templates:
            content = _custom_templates[id]["content"]
        else:
            # Check manager's custom_templates cache
            for (action, name), template in template_manager.custom_templates.items():
                if template.name == id:
                    content = template.user_prompt_template
                    break

            if content is None:
                all_templates = template_manager.list_templates()
                for template in all_templates:
                    if template.name == id:
                        content = template.user_prompt_template
                        break

        if content is None:
            logger.warning(
                "Attempted to preview non-existent template",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": id,
                },
            )
            raise HTTPException(status_code=404, detail=f"Template not found: {id}")

        # Render template using Jinja2
        try:
            jinja_template = Jinja2Template(content)
            rendered = jinja_template.render(**request.variables)
        except UndefinedError as e:
            logger.warning(
                "Template rendering failed - undefined variable",
                extra={
                    "user_id": current_user.get("user_id"),
                    "template_name": id,
                    "error": str(e),
                },
            )
            raise HTTPException(
                status_code=400,
                detail=f"Missing required variable: {str(e)}",
            )

        response_data = TemplatePreviewResponse(
            name=id,
            rendered=rendered,
        )

        logger.info(
            "Template preview rendered",
            extra={
                "user_id": current_user.get("user_id"),
                "template_name": id,
            },
        )

        return APIResponse(success=True, data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error previewing template",
            extra={"error": str(e), "template_name": id},
        )
        raise HTTPException(status_code=500, detail="Failed to preview template")
