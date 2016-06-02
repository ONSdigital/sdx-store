package com.github.onsdigital.sdxstore.json;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.apache.commons.lang3.StringUtils;

/**
 * Enables you to access elements and values from Json by path.
 * <p>
 * For example:
 * <ul>
 * <li>{@code person.name} returns the value "David" for the Json {@code {"person": {"name": "David"}}}</li>
 * <li>{@code address.1} returns the value "Middle Earth" for the Json {@code {"address": ["111 Hobiton Road", "Middle Earth"]}}</li>
 * <li>{@code books.0.author} returns the value "Laloux" for the Json {@code {"books": [{"name":"Reinventing Organizations", "author":"Laloux"}]}}</li>
 * </ul>
 */
public class Values {

    /**
     * Seaches for the given value within the given Json element and returns it as a String.
     *
     * @param path The path to be resolved.
     * @param json The Json element to search in.
     * @return If the path resolves to a Json primitive, this will be returned as a String.
     * If the path cannot be found or is not a primitive, null is returned.
     */
    public String getString(String path, JsonElement json) {
        JsonElement found = getElement(path, json);
        String result = null;
        if (found != null && found.isJsonPrimitive()) {
            result = found.getAsString();
        }
        return result;
    }

    /**
     * Seaches for the given path within the given Json element.
     *
     * @param path The path to be resolved.
     * @param json The Json element to search in.
     * @return If the path resolves to a Json element, this will be returned.
     * If the path cannot be found, null is returned.
     */
    public JsonElement getElement(String path, JsonElement json) {
        JsonElement found = json;
        String[] segments = StringUtils.split(path, '.');
        if (segments != null) {
            for (String segment : segments) {
                found = select(segment, found);
            }
        }
        return found;
    }

    /**
     * Selects a member of a Json object.
     *
     * @param name The name of the member to be selected.
     * @param json The element to look in.
     * @return If the given Json is a Json object, the matching member, if present.
     * If no member matches, or the Json is a primitive or array, null is returned.
     */
    JsonElement select(String name, JsonElement json) {
        JsonElement result = null;
        if (json != null) {
            if (json.isJsonObject()) {
                JsonObject object = (JsonObject) json;
                result = object.get(name);
            } else if (json.isJsonArray() && StringUtils.isNumeric(name)) {
                JsonArray array = (JsonArray) json;
                int index = Integer.parseInt(name);
                if (index >= 0 && index < array.size()) result = array.get(index);
            }
        }
        return result;
    }
}
