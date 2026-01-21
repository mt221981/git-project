"""WordPress REST API client."""

import requests
from typing import Dict, Any, List, Optional
from requests.auth import HTTPBasicAuth


class WordPressClientError(Exception):
    """Exception raised for WordPress API errors."""
    pass


class WordPressClient:
    """
    Client for interacting with WordPress REST API.

    Uses Application Passwords for authentication.
    """

    def __init__(self, site_url: str, username: str, password: str):
        """
        Initialize WordPress client.

        Args:
            site_url: WordPress site URL (e.g., https://example.com)
            username: WordPress username
            password: WordPress application password
        """
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = HTTPBasicAuth(username, password)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to WordPress API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/posts")
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            WordPressClientError: If request fails
        """
        url = f"{self.api_base}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                json=data,
                params=params,
                timeout=30
            )

            # Check for errors
            if response.status_code >= 400:
                error_msg = f"WordPress API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg = f"{error_msg} - {error_data['message']}"
                except:
                    pass
                raise WordPressClientError(error_msg)

            # Return JSON response
            if response.content:
                return response.json()
            return {}

        except requests.RequestException as e:
            raise WordPressClientError(f"Request failed: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to WordPress site.

        Returns:
            Site information

        Raises:
            WordPressClientError: If connection fails
        """
        # Get site info
        response = requests.get(f"{self.site_url}/wp-json", timeout=10)
        if response.status_code != 200:
            raise WordPressClientError("Cannot connect to WordPress site")

        site_info = response.json()

        # Test authentication
        try:
            self._request("GET", "/users/me")
        except WordPressClientError as e:
            raise WordPressClientError(f"Authentication failed: {str(e)}")

        return site_info

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        excerpt: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        author: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new WordPress post.

        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status (draft, publish, pending, private)
            excerpt: Post excerpt
            categories: List of category IDs
            tags: List of tag IDs
            author: Author ID
            meta: Custom meta fields

        Returns:
            Created post data

        Raises:
            WordPressClientError: If creation fails
        """
        data = {
            "title": title,
            "content": content,
            "status": status
        }

        if excerpt:
            data["excerpt"] = excerpt

        if categories:
            data["categories"] = categories

        if tags:
            data["tags"] = tags

        if author:
            data["author"] = author

        if meta:
            data["meta"] = meta

        return self._request("POST", "/posts", data=data)

    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        excerpt: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing WordPress post.

        Args:
            post_id: Post ID to update
            title: New title
            content: New content
            status: New status
            excerpt: New excerpt
            categories: New categories
            tags: New tags
            meta: New meta fields

        Returns:
            Updated post data

        Raises:
            WordPressClientError: If update fails
        """
        data = {}

        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if status is not None:
            data["status"] = status
        if excerpt is not None:
            data["excerpt"] = excerpt
        if categories is not None:
            data["categories"] = categories
        if tags is not None:
            data["tags"] = tags
        if meta is not None:
            data["meta"] = meta

        return self._request("PUT", f"/posts/{post_id}", data=data)

    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a post by ID."""
        return self._request("GET", f"/posts/{post_id}")

    def delete_post(self, post_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Delete a post.

        Args:
            post_id: Post ID to delete
            force: If True, permanently delete. If False, move to trash.

        Returns:
            Deleted post data
        """
        params = {"force": force}
        return self._request("DELETE", f"/posts/{post_id}", params=params)

    def get_categories(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Get all categories.

        Args:
            per_page: Number of categories per page (max 100)

        Returns:
            List of categories
        """
        params = {"per_page": per_page}
        return self._request("GET", "/categories", params=params)

    def create_category(self, name: str, description: Optional[str] = None, parent: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new category.

        Args:
            name: Category name
            description: Category description
            parent: Parent category ID

        Returns:
            Created category data
        """
        data = {"name": name}
        if description:
            data["description"] = description
        if parent:
            data["parent"] = parent

        return self._request("POST", "/categories", data=data)

    def get_tags(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get all tags."""
        params = {"per_page": per_page}
        return self._request("GET", "/tags", params=params)

    def create_tag(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new tag.

        Args:
            name: Tag name
            description: Tag description

        Returns:
            Created tag data
        """
        data = {"name": name}
        if description:
            data["description"] = description

        return self._request("POST", "/tags", data=data)

    def get_or_create_tags(self, tag_names: List[str]) -> List[int]:
        """
        Get or create tags by name and return their IDs.

        Args:
            tag_names: List of tag names

        Returns:
            List of tag IDs
        """
        if not tag_names:
            return []

        # Get existing tags
        existing_tags = self.get_tags()
        existing_map = {tag["name"].lower(): tag["id"] for tag in existing_tags}

        tag_ids = []
        for name in tag_names:
            name_lower = name.lower()
            if name_lower in existing_map:
                tag_ids.append(existing_map[name_lower])
            else:
                # Create new tag
                new_tag = self.create_tag(name)
                tag_ids.append(new_tag["id"])

        return tag_ids

    def update_yoast_seo(
        self,
        post_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        focus_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update Yoast SEO fields for a post.

        Args:
            post_id: Post ID
            title: SEO title
            description: Meta description
            focus_keyword: Focus keyword

        Returns:
            Updated post data

        Note:
            Requires Yoast SEO plugin installed and REST API enabled
        """
        # Use Yoast REST API directly
        yoast_data = {
            "yoast_head_json": {}
        }

        # Also try standard meta approach
        meta = {}
        if title:
            meta["_yoast_wpseo_title"] = title
            meta["yoast_wpseo_title"] = title
        if description:
            meta["_yoast_wpseo_metadesc"] = description
            meta["yoast_wpseo_metadesc"] = description
        if focus_keyword:
            meta["_yoast_wpseo_focuskw"] = focus_keyword
            meta["yoast_wpseo_focuskw"] = focus_keyword

        print(f"[Yoast] Sending meta update with field names: {list(meta.keys())}")

        # Try updating via standard post meta
        result = self.update_post(post_id, meta=meta)
        print(f"[Yoast] Standard meta response: {result.get('meta', 'NO META')}")

        # Try Yoast-specific REST endpoint
        try:
            yoast_url = f"{self.site_url}/wp-json/yoast/v1/post/{post_id}"
            yoast_payload = {
                "wpseo_title": title or "",
                "wpseo_metadesc": description or "",
                "wpseo_focuskw": focus_keyword or ""
            }
            print(f"[Yoast] Trying Yoast REST API: {yoast_url}")
            yoast_response = requests.put(
                yoast_url,
                auth=self.auth,
                json=yoast_payload,
                timeout=30
            )
            print(f"[Yoast] Yoast REST API response: {yoast_response.status_code}")
            if yoast_response.status_code == 200:
                print("[Yoast] Successfully updated via Yoast REST API")
            else:
                print(f"[Yoast] Yoast REST API failed: {yoast_response.text[:200]}")
        except Exception as e:
            print(f"[Yoast] Yoast REST API error: {e}")

        return result

    def update_rankmath_seo(
        self,
        post_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        focus_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update Rank Math SEO fields for a post.

        Args:
            post_id: Post ID
            title: SEO title
            description: Meta description
            focus_keyword: Focus keyword

        Returns:
            Updated post data

        Note:
            Requires Rank Math plugin installed
        """
        meta = {}
        if title:
            meta["rank_math_title"] = title
        if description:
            meta["rank_math_description"] = description
        if focus_keyword:
            meta["rank_math_focus_keyword"] = focus_keyword

        return self.update_post(post_id, meta=meta)
