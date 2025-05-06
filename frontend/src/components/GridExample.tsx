import Grid from '@mui/material/Unstable_Grid2';

const GridExampleCorrect = () => (
  <Grid container spacing={3}>
    <Grid xs={12} md={6}>
      {/* Content goes here */}
    </Grid>
    <Grid xs={12} md={6}>
      {/* More content */}
    </Grid>
  </Grid>
);

export default GridExampleCorrect;