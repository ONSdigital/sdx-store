package com.github.onsdigital.sdxstore;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.ArrayUtils;
import org.apache.commons.lang3.StringUtils;

import java.io.File;
import java.io.IOException;
import java.util.*;

/**
 * Playing with simple Json templating in Java.
 */
public class Tempuslate {

    public static void main(String[] args) throws IOException {

        // Read in Json data
        String string = FileUtils.readFileToString(new File("./test.json"));
        JsonObject json = new JsonParser().parse(string).getAsJsonObject();

        // Read in template
        String template = FileUtils.readFileToString(new File("./template.txt"));

        // Render
        tempuslate(json, template);
    }

    /**
     * Renders the given Json data using the given template.
     * @param json The data structure being used to populate this template.
     * @param template The template to be rendered.
     */
    public static void tempuslate(JsonElement json, String template) {
        //System.out.println("Template: " + template);
        List<String> chunks = parse(template);
        //System.out.println("---");
        Map<String, JsonElement> variables = new HashMap<>();
        int chunk = 0;
        while (chunk < chunks.size()) {
            //System.out.println("@"+chunk+"\\");
            chunk += process(chunks, chunk, json, variables);
        }
    }

    /**
     * Processes the chunk specified by {@code index}.
     * If the chunk is a loop, this method needs access to
     * the chunks that make up the loop, which is why the
     * full list of chunks is passed in.
     * <p>
     * NB nested loops aren't supported.
     *
     * @param chunks The list of chunks for this template.
     * @param index The index of the chunk to be processed.
     * @param json The data structure being used to populate this template.
     * @param variables Contains any variables that have been set,
     *                  such as assigning a json path, or a loop variable.
     * @return The number of chunks to move forward in the list, which is normally 1.
     *          However, if we've just processed a loop, this will be more than one
     *          in order to advance past the {@code {{end}}} marker.
     */
    private static int process(List<String> chunks, int index, JsonElement json, Map<String, JsonElement> variables) {
        int result = 1;
        String chunk = chunks.get(index);
        if (!StringUtils.startsWith(chunk, "{{")) {

            // Text content
            System.out.print(chunk);

        } else {

            // Remove braces from the instruction
            String instruction = chunk.substring(2, chunk.length() - 2).trim();
            String[] parts = instruction.split(" ");

            if (parts.length == 1) {

                // Simple print
                JsonElement element = resolve(instruction, json, variables);
                print(element);

            } else if (parts.length == 3) {

                if (StringUtils.equalsIgnoreCase("as", parts[1])) {

                    // Assign a variable: {{select.path as variable}}
                    variables.put(parts[2], find(parts[0], json));

                } else if (StringUtils.equalsIgnoreCase("in", parts[1])) {

                    // Loop: {{variable in array.element}}

                    // Extract the chunks of the loop (whether or not we actually run any interations):
                    List<String> loopChunks = new ArrayList<>();
                    String loopChunk;
                    while (!StringUtils.equalsIgnoreCase(loopChunk = chunks.get(index + result++), "{{end}}")) {
                        loopChunks.add(loopChunk);
                    }

                    // Get the array to be iterated
                    JsonElement element = resolve(parts[2], json, variables);
                    if (element != null && element.isJsonArray()) {

                        // Iterate the array
                        JsonArray array = (JsonArray) element;
                        for (int i = 0; i < array.size(); i++) {
                            Map<String, JsonElement> loopVariables = new HashMap<>(variables);
                            loopVariables.put(parts[0], array.get(i));

                            // Run the loop chunks
                            int counter = 0;
                            while (counter < loopChunks.size()) {
                                counter += process(loopChunks, counter, json, loopVariables);
                            }
                        }
                    }

                } else {

                    // Not implemented or invalid, so just print:
                    System.out.print(chunk);
                }
            }
        }

        return result;
    }

    /**
     * Resolves a Json path, first against any variables and second against the Json data structure.
     * @param path The Json path to be resolved.
     * @param json The Json data structure.
     * @param variables Any variables that have been assigned.
     * @return If the path can be resolved to one of the variables (or a sub-element of one of the variables)
     *          this will be returned. If no variable matches but the path can be resolved within the
     *          Json data structure, then that element will be returned. If neither matches, null is returned.
     */
    static JsonElement resolve(String path, JsonElement json, Map<String, JsonElement> variables) {
        JsonElement result;

        String[] segments = path.split("\\.");
        JsonElement variable = segments.length > 0 ? variables.get(segments[0]) : null;
        if (variable != null) {
            // Select the variable
            if (segments.length == 1) {
                result = variable;
            } else {
                // Select any additional path under the variable
                segments = ArrayUtils.subarray(segments, 1, segments.length);
                path = StringUtils.join(segments, '.');
                result = find(path, variable);
            }
        } else {
            // Select from the root level
            result = find(path, json);
        }

        return result;
    }

    /**
     * Seaches for the given path within the given Json element.
     * @param path The path to be resolved.
     * @param json The Json element to search in.
     * @return If the path resolves to a Json element, this will be returned.
     *          If the path cannot be found, null is returned.
     */
    static JsonElement find(String path, JsonElement json) {
        JsonElement element = null;
        if (StringUtils.isNotBlank(path)) {
            String[] segments = path.split("\\.");
            element = StringUtils.isNotBlank(path) ? json : null;
            for (String segment : segments) {
                element = select(segment, element);
            }
        }
        return element;
    }

    /**
     * Selects a member of a Json object.
     * @param name The name of the member to be selected.
     * @param json The element to look in.
     * @return If the given Json is a Json object, the matching member, if present.
     *          If no member matches, or the Json is a primitive or array, null is returned.
     */
    static JsonElement select(String name, JsonElement json) {
        JsonElement result = null;
        if (json != null && json.isJsonObject()) {
            JsonObject object = (JsonObject) json;
            if (object.has(name)) {
                result = object.get(name);
            }
        }
        return result;
    }

    /**
     * Prints out the given Json element. If the element is a primitive, the value is 'got' as a String,
     * otherwise the element is printed as Json.
     * @param element The element to be printed.
     */
    static void print(JsonElement element) {
        if (element != null && element.isJsonPrimitive()) {
            System.out.print(element.getAsString());
        } else {
            System.out.print(element);
        }
    }

    /**
     * Parses the given template content into a list of 'chunks' for processing.
     * A chunk is either a piece of plain content, or a processing instruction.
     * @param template The template content.
     * @return A list of all chunks parsed from the template content.
     */
    static List<String> parse(String template) {
        List<String> chunks = new ArrayList<>();
        int position = 0;
        while (position < template.length()) {
            int start = template.indexOf("{{", position);
            if (start > position) {
                String chunk = template.substring(position, start);
                chunks.add(chunk);
            }
            if (start != -1) {
                int end = template.indexOf("}}", start);
                if (end != -1) {
                    end += 2;
                } else {
                    // Unclosed so consume to the end and quit:
                    end = template.length();
                }
                String chunk = template.substring(start, end);
                chunks.add(chunk);
                position = end;
            } else {
                chunks.add(template.substring(position));
                position = template.length();
            }
        }
        return chunks;
    }
}

