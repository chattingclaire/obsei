"""
Configuration Routes for Data Agent and Classify Agent
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import yaml
import json
import os

router = APIRouter()


# Configuration endpoints for Data Agent
@router.get("/config/data_agent")
def get_data_agent_config():
    """Get data agent configuration"""
    try:
        with open("config/settings.yaml", "r") as f:
            settings = yaml.safe_load(f)

        data_agent_config = settings.get("agents", {}).get("data_agent", {})
        return {
            "sources": data_agent_config.get("sources", {}),
            "batch_size": data_agent_config.get("batch_size", 100),
            "interval_seconds": data_agent_config.get("interval_seconds", 300)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/data_agent/sources/{source_name}")
def update_data_source(source_name: str, update: Dict[str, Any]):
    """Update data source configuration"""
    try:
        with open("config/settings.yaml", "r") as f:
            settings = yaml.safe_load(f)

        if "agents" not in settings:
            settings["agents"] = {}
        if "data_agent" not in settings["agents"]:
            settings["agents"]["data_agent"] = {}
        if "sources" not in settings["agents"]["data_agent"]:
            settings["agents"]["data_agent"]["sources"] = {}

        # Update source
        if source_name not in settings["agents"]["data_agent"]["sources"]:
            settings["agents"]["data_agent"]["sources"][source_name] = {}

        settings["agents"]["data_agent"]["sources"][source_name].update(update)

        with open("config/settings.yaml", "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

        return {"status": "updated", "source": source_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/data_agent/sources/{source_name}/accounts")
def add_account_to_source(source_name: str, account_data: Dict[str, str]):
    """Add account to data source"""
    try:
        with open("config/settings.yaml", "r") as f:
            settings = yaml.safe_load(f)

        source_config = settings["agents"]["data_agent"]["sources"].get(source_name, {})

        if "accounts" not in source_config:
            source_config["accounts"] = []

        if account_data.get("account") not in source_config["accounts"]:
            source_config["accounts"].append(account_data["account"])

        settings["agents"]["data_agent"]["sources"][source_name] = source_config

        with open("config/settings.yaml", "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

        return {"status": "added", "account": account_data["account"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/config/data_agent/sources/{source_name}/accounts/{account}")
def remove_account_from_source(source_name: str, account: str):
    """Remove account from data source"""
    try:
        with open("config/settings.yaml", "r") as f:
            settings = yaml.safe_load(f)

        source_config = settings["agents"]["data_agent"]["sources"].get(source_name, {})

        if "accounts" in source_config and account in source_config["accounts"]:
            source_config["accounts"].remove(account)

        settings["agents"]["data_agent"]["sources"][source_name] = source_config

        with open("config/settings.yaml", "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

        return {"status": "removed", "account": account}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints for Classify Agent
@router.get("/config/taxonomy")
def get_taxonomy():
    """Get classification taxonomy"""
    try:
        with open("config/taxonomy.json", "r") as f:
            taxonomy = json.load(f)
        return taxonomy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/classify_agent/custom_fields")
def get_custom_fields():
    """Get custom classification fields"""
    try:
        try:
            with open("config/custom_fields.json", "r") as f:
                fields = json.load(f)
        except FileNotFoundError:
            fields = {"fields": []}

        return fields
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/classify_agent/custom_fields")
def add_custom_field(field_data: Dict[str, Any]):
    """Add custom classification field"""
    try:
        try:
            with open("config/custom_fields.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {"fields": []}

        config["fields"].append(field_data)

        with open("config/custom_fields.json", "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return {"status": "added", "field": field_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/config/classify_agent/custom_fields/{field_name}")
def remove_custom_field(field_name: str):
    """Remove custom classification field"""
    try:
        with open("config/custom_fields.json", "r") as f:
            config = json.load(f)

        config["fields"] = [f for f in config["fields"] if f["name"] != field_name]

        with open("config/custom_fields.json", "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return {"status": "removed", "field_name": field_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
