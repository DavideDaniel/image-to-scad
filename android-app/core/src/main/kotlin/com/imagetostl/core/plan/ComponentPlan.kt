package com.imagetostl.core.plan

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** Mirrors the `component-plan/v0` schema produced by scripts/blender_build_components.py. */
@Serializable
data class ComponentPlan(
    val schema: String = "component-plan/v0",
    val units: String = "mm",
    val model: Model,
)

@Serializable
data class Model(
    val name: String,
    val bevel: Double = 0.0,
    val components: List<Component>,
    val cuts: List<Component> = emptyList(),
)

@Serializable
data class Component(
    val name: String,
    val type: String, // "box" | "cylinder"
    val size: List<Double>? = null, // box: [x, y, z] full extents
    val radius: Double? = null, // cylinder
    val depth: Double? = null, // cylinder
    val axis: String? = null, // cylinder: "x" | "y" | "z"
    val vertices: Int? = null, // cylinder tessellation, default 64
    val center: List<Double>,
)

private val planJson = Json {
    ignoreUnknownKeys = true // plans carry extra provenance fields (measurements, source_images, ...) we don't model
    isLenient = true
}

fun parseComponentPlan(json: String): ComponentPlan = planJson.decodeFromString(ComponentPlan.serializer(), json)
