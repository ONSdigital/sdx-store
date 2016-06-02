package com.github.onsdigital.sdxstore.json;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import org.apache.commons.lang3.StringUtils;

import java.util.HashMap;
import java.util.Map;

/**
 * Playing with simple Json templating in Java.
 */
public class Keys {

    /**
     * Gets all paths in the given Json.
     * @param json The Json to examine.
     * @return A map of paths to Json types.
     */
    public Map<String, Class<? extends JsonElement>> getPaths(JsonElement json) {
        Map<String, Class<? extends JsonElement>> paths = new HashMap<>();
        if (json.isJsonPrimitive()) paths.put("", JsonPrimitive.class);
        if (json.isJsonArray()) paths.put("", JsonArray.class);
        if (json.isJsonObject()) {
            for (Map.Entry<String, JsonElement> entry : ((JsonObject)json).entrySet()) {
                String member = entry.getKey();
                Class<? extends JsonElement> type = entry.getValue().getClass();
                paths.put(member, type);
            }
        }
        return paths;
    }

    /**
     * Gets all paths in the given Json that point to a {@link JsonPrimitive}.
     * @param json The Json to examine.
     * @return A map of paths to Json elements.
     */
    public Map<String, Class<? extends JsonElement>> getPrivitivePaths(JsonElement json) {
        Map<String, Class<? extends JsonElement>> paths = new HashMap<>();
        if (json.isJsonPrimitive()) paths.put("", JsonPrimitive.class);
        if (json.isJsonArray()) paths.put("", JsonArray.class);
        if (json.isJsonObject()) {
            for (Map.Entry<String, JsonElement> entry : ((JsonObject)json).entrySet()) {
                String member = entry.getKey();
                Class<? extends JsonElement> type = entry.getValue().getClass();
                paths.put(member, type);
            }
        }
        return paths;
    }

    /**
     * Gets all paths at the given {@link JsonElement}.
     * @param json The Json to examine.
     * @return This will returnn eithe:
     * <ul>
     *    <li>"" mapped to a {@link JsonPrimitive};</li>
     *    <li>"" mapped to a {@link JsonArray}; or</li>
     *    <li>if the given Json is a {@link JsonObject}, the members of the object</li>
     * </ul>
     */
    Map<String, Class<? extends JsonElement>> getLocalPaths(JsonElement json, Map<String, Class<? extends JsonElement>> paths) {
        if (json.isJsonPrimitive()) paths.put("", JsonPrimitive.class);
        if (json.isJsonArray()) paths.put("", JsonArray.class);
        if (json.isJsonObject()) {
            for (Map.Entry<String, JsonElement> entry : ((JsonObject)json).entrySet()) {
                String member = entry.getKey();
                Class<? extends JsonElement> type = entry.getValue().getClass();
                paths.put(member, type);
            }
        }
        return paths;
    }

    public Map<String, Class<? extends JsonElement>> getAllPrimitivePaths(JsonElement json) {
        Map<String, Class<? extends JsonElement>> keys = new HashMap<>();
        String key = "";
        add(key, json, keys);
        return keys;
    }

    void add(String key, JsonElement json, Map<String, Class<? extends JsonElement>> paths) {
        if (json.isJsonPrimitive()) add(key, (JsonPrimitive) json, paths);
        if (json.isJsonArray()) add(key, (JsonArray) json, paths);
        if (json.isJsonObject()) add(key, (JsonObject) json, paths);
    }

    /**
     * Adds the path to a {@link JsonPrimitive} to the set of found paths.
     * @param path The path to this {@link JsonPrimitive}.
     * @param json The Json of this {@link JsonPrimitive}.
     * @param paths The set of paths to add the path of this primitive to.
     */
    void add(String path, JsonPrimitive json, Map<String, Class<? extends JsonElement>>  paths) {
        paths.put(path, json.getClass());
    }

    /**
     * Searches through the indices of a {@link JsonArray}, recursing to find paths to primitive values.
     * @param path The path to this {@link JsonArray}.
     * @param json The Json of this {@link JsonArray}.
     * @param paths The set of paths to (eventually) add any results to.
     */
    void add(String path, JsonArray json, Map<String, Class<? extends JsonElement>>  paths) {
        String arrayKey = path;
        for (int i = 0; i < json.size(); i++) {
            add(arrayKey + "." + i, json.get(i), paths);
        }
    }

    /**
     * Searches through the members of a {@link JsonObject}}, recursing to find paths to primitive values.
     * @param path The path to this {@link JsonObject}.
     * @param json The Json of this {@link JsonObject}.
     * @param paths The set of paths to (eventually) add any results to.
     */
    void add(String path, JsonObject json, Map<String, Class<? extends JsonElement>>  paths) {
        for (Map.Entry<String, JsonElement> member : json.entrySet()) {
            String memberName = member.getKey();
            JsonElement memberJson = member.getValue();
            String memberKey = key(path, memberName);
            add(memberKey, memberJson, paths);
        }
    }

    /**
     * Adds the given name to the given base path.
     *
     * @param path The base path to add the name to.
     * @param name  The name to add to the end of the path.
     * @return If the base is blank, "{@code key}". If the base is not blank, "{@code base.key}".
     */
    String key(String path, String name) {
        return (StringUtils.isNotBlank(path) ? path + "." : "") + name;
    }
}

