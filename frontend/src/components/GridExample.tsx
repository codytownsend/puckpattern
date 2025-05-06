import { Grid } from '@mui/material';

const GridExampleCorrect = () => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={6}>
      {/* Content goes here */}
    </Grid>
    <Grid item xs={12} md={6}>
      {/* More content */}
    </Grid>
  </Grid>
);

export default GridExampleCorrect;