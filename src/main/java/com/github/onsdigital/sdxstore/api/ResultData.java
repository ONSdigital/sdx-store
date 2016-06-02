package com.github.onsdigital.sdxstore.api;

import com.google.gson.JsonElement;

/**
 * Represents the data of a survey response retrieved from the SDX store.
 */
public class ResultData {

    /** The stored Json of the survey response. */
    public JsonElement surveyResponse;

    /** The readable date that this survey response was stored. */
    public String addedDate;

    /** The searchable date that this survey response was stored. */
    public String addedMs;

}
