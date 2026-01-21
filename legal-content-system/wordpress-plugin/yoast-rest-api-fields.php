<?php
/**
 * Plugin Name: Yoast SEO REST API Fields
 * Description: Exposes Yoast SEO meta fields to WordPress REST API for external publishing systems
 * Version: 1.0.0
 * Author: LT-Law System
 * Text Domain: yoast-rest-api-fields
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Register Yoast SEO meta fields for REST API
 */
add_action('init', function() {
    // Only run if Yoast SEO is active
    if (!defined('WPSEO_VERSION')) {
        return;
    }

    $yoast_fields = [
        '_yoast_wpseo_title' => [
            'description' => 'Yoast SEO Title',
            'type' => 'string',
        ],
        '_yoast_wpseo_metadesc' => [
            'description' => 'Yoast Meta Description',
            'type' => 'string',
        ],
        '_yoast_wpseo_focuskw' => [
            'description' => 'Yoast Focus Keyword',
            'type' => 'string',
        ],
    ];

    // Register for posts and pages
    $post_types = ['post', 'page'];

    foreach ($post_types as $post_type) {
        foreach ($yoast_fields as $field_name => $field_config) {
            register_post_meta($post_type, $field_name, [
                'show_in_rest' => true,
                'single' => true,
                'type' => $field_config['type'],
                'description' => $field_config['description'],
                'auth_callback' => function() {
                    return current_user_can('edit_posts');
                },
            ]);
        }
    }
}, 20); // Priority 20 to run after Yoast initializes

/**
 * Also expose fields without underscore prefix (for compatibility)
 */
add_action('rest_api_init', function() {
    register_rest_field(['post', 'page'], 'yoast_meta', [
        'get_callback' => function($post) {
            return [
                'title' => get_post_meta($post['id'], '_yoast_wpseo_title', true),
                'description' => get_post_meta($post['id'], '_yoast_wpseo_metadesc', true),
                'focus_keyword' => get_post_meta($post['id'], '_yoast_wpseo_focuskw', true),
            ];
        },
        'update_callback' => function($value, $post) {
            if (!current_user_can('edit_post', $post->ID)) {
                return new WP_Error('rest_forbidden', 'Permission denied', ['status' => 403]);
            }

            if (isset($value['title'])) {
                update_post_meta($post->ID, '_yoast_wpseo_title', sanitize_text_field($value['title']));
            }
            if (isset($value['description'])) {
                update_post_meta($post->ID, '_yoast_wpseo_metadesc', sanitize_text_field($value['description']));
            }
            if (isset($value['focus_keyword'])) {
                update_post_meta($post->ID, '_yoast_wpseo_focuskw', sanitize_text_field($value['focus_keyword']));
            }

            return true;
        },
        'schema' => [
            'type' => 'object',
            'properties' => [
                'title' => ['type' => 'string'],
                'description' => ['type' => 'string'],
                'focus_keyword' => ['type' => 'string'],
            ],
        ],
    ]);
});
