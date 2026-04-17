import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { init, use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';

// Centralize the minimal ECharts runtime we currently need.
use([LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

export { init };
