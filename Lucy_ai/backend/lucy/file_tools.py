import os
import shutil
import fnmatch
from typing import Any, Dict, List
from lucy.tools import LucyTool, registry

# Root workspace directory for validation
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Lucy_workspace"))

def resolve_safe_path(path: str, restrict_to_workspace: bool = True) -> str:
    """Resolve a path to its absolute location.
    If restrict_to_workspace is True, ensures the path lies inside WORKSPACE_DIR.
    """
    path_clean = path.strip()
    
    # If path is relative, resolve it against workspace directory
    if not os.path.isabs(path_clean):
        abs_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path_clean))
    else:
        abs_path = os.path.abspath(path_clean)
        
    # Security check: verify path is inside WORKSPACE_DIR if restricted
    if restrict_to_workspace:
        # Common prefix check to prevent directory traversal (e.g., path/../../etc)
        if not abs_path.startswith(WORKSPACE_DIR):
            raise PermissionError(f"Access Denied: Path '{abs_path}' lies outside the allowed workspace '{WORKSPACE_DIR}'.")
            
    return abs_path


class FileSearchTool(LucyTool):
    name = "file_search"
    description = "Search for files by name matching a wildcard pattern (e.g. '*.txt') or containing specific text content inside the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Wildcard pattern to match filenames (e.g. '*.txt', 'shopping*', '*invoice*'). Defaults to '*'"
            },
            "search_content": {
                "type": "string",
                "description": "Optional text query to find within file contents."
            },
            "subfolder": {
                "type": "string",
                "description": "Optional subdirectory to limit search (e.g. 'notes', 'projects'). Defaults to search entire workspace."
            }
        },
        "required": []
    }

    async def run(self, pattern: str = "*", search_content: str = None, subfolder: str = None) -> Dict[str, Any]:
        search_root = resolve_safe_path(subfolder if subfolder else "", restrict_to_workspace=True)
        results = []

        try:
            for root, dirs, files in os.walk(search_root):
                for filename in fnmatch.filter(files, pattern):
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, WORKSPACE_DIR)
                    
                    matched = True
                    if search_content:
                        matched = False
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                if search_content.lower() in f.read().lower():
                                    matched = True
                        except Exception:
                            pass # Skip files that cannot be read as text

                    if matched:
                        results.append({
                            "filename": filename,
                            "path": relative_path.replace("\\", "/"),
                            "size_bytes": os.path.getsize(filepath)
                        })

            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"status": "error", "message": f"Search failed: {str(e)}"}


class FileReadTool(LucyTool):
    name = "file_read"
    description = "Read the contents of a text file inside the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The path of the file to read (relative to the workspace root, e.g. 'notes/todo.txt')."
            }
        },
        "required": ["filepath"]
    }

    async def run(self, filepath: str) -> Dict[str, Any]:
        try:
            # We allow reading outside workspace only if it is explicitly in user profile
            # For Phase 2, we restrict reads to workspace or standard system paths
            # Let's restrict to workspace for safety first
            abs_path = resolve_safe_path(filepath, restrict_to_workspace=True)
            
            if not os.path.exists(abs_path):
                return {"status": "error", "message": f"File does not exist: {filepath}"}
                
            if os.path.isdir(abs_path):
                return {"status": "error", "message": f"Path is a directory, not a file: {filepath}"}

            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return {
                "status": "success",
                "filepath": filepath,
                "content": content
            }
        except PermissionError as pe:
            return {"status": "error", "message": str(pe)}
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {str(e)}"}


class FileWriteTool(LucyTool):
    name = "file_write"
    description = "Write or append text content to a file inside the workspace. Automatically creates directories if missing."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The path of the file to write to (relative to the workspace root, e.g., 'notes/shopping_list.txt')."
            },
            "content": {
                "type": "string",
                "description": "The exact text content to write into the file."
            },
            "mode": {
                "type": "string",
                "description": "Write mode: 'overwrite' to replace content, 'append' to add to the end of the file.",
                "enum": ["overwrite", "append"]
            }
        },
        "required": ["filepath", "content"]
    }

    async def run(self, filepath: str, content: str, mode: str = "overwrite") -> Dict[str, Any]:
        try:
            abs_path = resolve_safe_path(filepath, restrict_to_workspace=True)
            
            # Create directories if they do not exist
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            write_mode = 'a' if mode == 'append' else 'w'
            with open(abs_path, write_mode, encoding='utf-8') as f:
                f.write(content)
                
            return {
                "status": "success",
                "filepath": filepath,
                "mode": mode,
                "message": f"Successfully written to file."
            }
        except PermissionError as pe:
            return {"status": "error", "message": str(pe)}
        except Exception as e:
            return {"status": "error", "message": f"Failed to write file: {str(e)}"}


class FileCreateTool(LucyTool):
    name = "file_create"
    description = "Create an empty file or a new folder subdirectory inside the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path of the file or directory to create (relative to the workspace root, e.g. 'projects/lucy_app')."
            },
            "type": {
                "type": "string",
                "description": "Type of item to create: 'file' or 'directory'.",
                "enum": ["file", "directory"]
            }
        },
        "required": ["path"]
    }

    async def run(self, path: str, type: str = "file") -> Dict[str, Any]:
        try:
            abs_path = resolve_safe_path(path, restrict_to_workspace=True)
            
            if os.path.exists(abs_path):
                return {"status": "error", "message": f"Path already exists: {path}"}

            if type == "directory":
                os.makedirs(abs_path, exist_ok=True)
                message = f"Created directory: {path}"
            else:
                # Create parent folders if missing
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    pass # Create empty file
                message = f"Created empty file: {path}"

            return {
                "status": "success",
                "path": path,
                "type": type,
                "message": message
            }
        except PermissionError as pe:
            return {"status": "error", "message": str(pe)}
        except Exception as e:
            return {"status": "error", "message": f"Failed to create item: {str(e)}"}


class FileMoveTool(LucyTool):
    name = "file_move"
    description = "Copy, move, or rename files/directories inside the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "src": {
                "type": "string",
                "description": "The source path (relative to the workspace root, e.g. 'downloads/invoice.pdf')."
            },
            "dest": {
                "type": "string",
                "description": "The destination path (relative to the workspace root, e.g. 'notes/invoice_final.pdf')."
            },
            "action": {
                "type": "string",
                "description": "Action to perform: 'move' (cut/paste/rename), 'copy' (duplicate).",
                "enum": ["move", "copy"]
            }
        },
        "required": ["src", "dest"]
    }

    async def run(self, src: str, dest: str, action: str = "move") -> Dict[str, Any]:
        try:
            abs_src = resolve_safe_path(src, restrict_to_workspace=True)
            abs_dest = resolve_safe_path(dest, restrict_to_workspace=True)

            if not os.path.exists(abs_src):
                return {"status": "error", "message": f"Source path does not exist: {src}"}

            # Create destination folder if missing
            os.makedirs(os.path.dirname(abs_dest), exist_ok=True)

            if action == "copy":
                if os.path.isdir(abs_src):
                    shutil.copytree(abs_src, abs_dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(abs_src, abs_dest)
                msg = f"Copied '{src}' to '{dest}'."
            else: # move
                shutil.move(abs_src, abs_dest)
                msg = f"Moved '{src}' to '{dest}'."

            return {
                "status": "success",
                "src": src,
                "dest": dest,
                "action": action,
                "message": msg
            }
        except PermissionError as pe:
            return {"status": "error", "message": str(pe)}
        except Exception as e:
            return {"status": "error", "message": f"Operation failed: {str(e)}"}

# Register all file tools
registry.register(FileSearchTool())
registry.register(FileReadTool())
registry.register(FileWriteTool())
registry.register(FileCreateTool())
registry.register(FileMoveTool())
