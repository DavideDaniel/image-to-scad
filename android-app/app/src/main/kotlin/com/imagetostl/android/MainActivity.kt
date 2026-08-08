package com.imagetostl.android

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.FileProvider
import com.imagetostl.android.gl.MeshGLSurfaceView
import com.imagetostl.core.assembly.PlanBuilder
import com.imagetostl.core.mesh.Mesh
import com.imagetostl.core.plan.ComponentPlan
import com.imagetostl.core.plan.editableParameters
import com.imagetostl.core.plan.parseComponentPlan
import com.imagetostl.core.plan.withParameterValue
import com.imagetostl.core.stl.StlWriter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

/**
 * Loads the bundled sample component-plan; a file/photo import flow is not
 * built yet (see android-app/README.md), so this is the one entry point for
 * now. Everything else - editing, preview, export - is fully functional.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val initialPlan = parseComponentPlan(
            assets.open("sample_plans/circular_shelf_plan.json").bufferedReader().readText()
        )
        setContent {
            MaterialTheme {
                ModelEditorScreen(initialPlan)
            }
        }
    }
}

@Composable
fun ModelEditorScreen(initialPlan: ComponentPlan) {
    val context = LocalContext.current
    var plan by remember { mutableStateOf(initialPlan) }
    var mesh by remember { mutableStateOf<Mesh?>(null) }
    var building by remember { mutableStateOf(true) }
    val baseline = remember { initialPlan.editableParameters() }
    val glView = remember { MeshGLSurfaceView(context) }

    LaunchedEffect(plan) {
        building = true
        val built = withContext(Dispatchers.Default) { PlanBuilder.build(plan) }
        mesh = built
        glView.setMesh(built)
        building = false
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text(plan.model.name) }) },
    ) { padding ->
        Column(modifier = Modifier.padding(padding).fillMaxSize()) {
            Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                AndroidView(factory = { glView }, modifier = Modifier.fillMaxSize())
                if (building) {
                    LinearProgressIndicator(
                        modifier = Modifier.align(Alignment.TopCenter).fillMaxWidth(),
                    )
                }
            }
            HorizontalDivider()

            val currentParams = plan.editableParameters()
            LazyColumn(modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 16.dp)) {
                items(baseline.size) { i ->
                    val base = baseline[i]
                    val current = currentParams[i]
                    val component =
                        if (base.fromCuts) plan.model.cuts[base.componentIndex] else plan.model.components[base.componentIndex]
                    ParameterSlider(
                        label = base.label(component),
                        value = current.value,
                        range = (base.value * 0.4)..(base.value * 2.5),
                        onValueChange = { newValue -> plan = plan.withParameterValue(current, newValue) },
                    )
                }
            }

            Button(
                onClick = {
                    mesh?.let { m ->
                        val file = exportStl(context, m, plan.model.name)
                        shareStl(context, file)
                    }
                },
                enabled = mesh != null && !building,
                modifier = Modifier.fillMaxWidth().padding(16.dp),
            ) {
                Text("Export STL")
            }
        }
    }
}

@Composable
private fun ParameterSlider(
    label: String,
    value: Double,
    range: ClosedFloatingPointRange<Double>,
    onValueChange: (Double) -> Unit,
) {
    Column(modifier = Modifier.padding(vertical = 6.dp)) {
        Text("$label: ${"%.1f".format(value)} mm", style = MaterialTheme.typography.bodyMedium)
        Slider(
            value = value.toFloat(),
            valueRange = range.start.toFloat()..range.endInclusive.toFloat(),
            onValueChange = { onValueChange(it.toDouble()) },
        )
    }
}

private fun exportStl(context: Context, mesh: Mesh, name: String): File {
    val dir = File(context.getExternalFilesDir(null), "exports").apply { mkdirs() }
    val file = File(dir, "$name.stl")
    FileOutputStream(file).use { out -> StlWriter.writeBinary(mesh, out) }
    return file
}

private fun shareStl(context: Context, file: File) {
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "model/stl"
        putExtra(Intent.EXTRA_STREAM, uri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Share STL"))
}
