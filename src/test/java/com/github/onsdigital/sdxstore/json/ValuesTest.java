package com.github.onsdigital.sdxstore.json;

import com.github.davidcarboni.ResourceUtils;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.IOException;

import static org.junit.Assert.*;

/**
 * Test for {@code Values}.
 * Created by david on 29/05/2016.
 */
public class ValuesTest {

    static String string;
    JsonElement json;
    Values values;

    @BeforeClass
    public static void beforeClass() throws IOException {
        string = ResourceUtils.getString("/test.json");
    }

    @Before
    public void before() {
        json = Argonaut.parse(string);
        values = new Values();
    }

    /**
     * Checks the possible paths to the root element.
     * It is expected that "" should be used, but the others work as well.
     */
    @Test
    public void shouldGetRootElement() {

        // Given
        String[] rootPaths = {"", null, "."};
        JsonElement[] results = new JsonElement[rootPaths.length];

        // When
        for (int i = 0; i < rootPaths.length; i++) {
            results[i] = values.getElement(rootPaths[i], json);
        }

        // Then
        for (int i = 0; i < results.length; i++) {
            assertNotNull(results[i]);
            assertTrue(results[i].isJsonObject());
            assertTrue(((JsonObject) results[i]).has("intro"));
            assertTrue(((JsonObject) results[i]).has("sections"));
        }
    }

    /**
     * Checks that getting a path to a primitive returns the String at that path.
     */
    @Test
    public void shouldGetPrimitiveAsString() {

        // Given
        String path = "intro.title";

        // When
        String result = values.getString(path, json);

        // Then
        assertNotNull(result);
        assertEquals("Welcome to the Office for National Statistics", result);
    }

    /**
     * Checks that null will be returned if the path points to an element, but a String is requested.
     */
    @Test
    public void shouldNotGetElementAsString() {

        // Given
        String path = "intro";

        // When
        String result = values.getString(path, json);

        // Then
        assertNull(result);
        assertTrue(((JsonObject) json).has(path));
    }

    @Test
    public void shouldGetPrimitiveFromArray() throws Exception {

        // Given
        String path = "description.keywords.2";

        // When
        String result = values.getString(path, json);

        // Then
        assertNotNull(result);
        assertEquals("census", result);
    }

    @Test
    public void shouldGetElementFromArray() throws Exception {

        // Given
        String path = "description.keywords.1";

        // When
        JsonElement result = values.getElement(path, json);

        // Then
        assertNotNull(result);
        assertTrue(result.isJsonPrimitive());
        assertEquals("economy", result.getAsString());
    }

    @Test
    public void shouldGetNullForArrayOutOfBounds() throws Exception {

        // Given
        String pathLow = "sections.-1";
        String pathHigh = "sections.5";

        // When
        JsonElement resultLow = values.getElement(pathLow, json);
        JsonElement resultHigh = values.getElement(pathHigh, json);

        // Then
        assertTrue(((JsonObject)json).has("sections"));
        assertNull(resultLow);
        assertNull(resultHigh);
    }

    @Test
    public void shouldGetPrimitive() throws Exception {

        // Given
        String value = "test";
        JsonElement json = Argonaut.parse("\"" + value + "\"");

        // When
        String result = values.getString("", json);

        // Then
        assertNotNull(result);
        assertEquals(value, result);
    }

}